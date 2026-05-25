# streamlit_legal_agent.py
import streamlit as st
import os
import re
import faiss
import pickle
import ollama
import fitz
from sentence_transformers import SentenceTransformer
from docx import Document

# ---------- Configuration ----------
DOCUMENTS_PATH = "./legal_docs"  # folder containing PDFs/DOCs/TXT
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_DB_FILE = "vector_index.faiss"
DOC_MAPPING_FILE = "doc_mapping.pkl"
LLM_MODEL = "gemma4:e4b"
CHUNK_SIZE = 500  # words

# ---------- Helper functions ----------
def load_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def load_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

def chunk_text(text, chunk_size=CHUNK_SIZE):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

def regex_redact(text):
    text = re.sub(r'\b\d{9}[VvXx]\b', '[REDACTED_NIC]', text)
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED_EMAIL]', text)
    text = re.sub(r'\b\d{10}\b', '[REDACTED_PHONE]', text)
    return text

# ---------- Build vector DB ----------
def build_vector_db():
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    index = faiss.IndexFlatL2(384)
    doc_mapping = {}
    idx = 0

    for file_name in os.listdir(DOCUMENTS_PATH):
        path = os.path.join(DOCUMENTS_PATH, file_name)
        if path.endswith(".pdf"):
            text = load_text_from_pdf(path)
        elif path.endswith(".docx"):
            text = load_text_from_docx(path)
        elif path.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            continue

        chunks = chunk_text(text)
        embeddings = embedder.encode(chunks)
        index.add(embeddings)
        for i, chunk in enumerate(chunks):
            doc_mapping[idx] = chunk
            idx += 1

    faiss.write_index(index, VECTOR_DB_FILE)
    with open(DOC_MAPPING_FILE, "wb") as f:
        pickle.dump(doc_mapping, f)

    st.success(f"Vector DB built with {idx} chunks.")

# ---------- Load vector DB ----------
def load_vector_db():
    index = faiss.read_index(VECTOR_DB_FILE)
    with open(DOC_MAPPING_FILE, "rb") as f:
        doc_mapping = pickle.load(f)
    return index, doc_mapping

# ---------- Retrieve top-k docs ----------
def retrieve(query, k=3):
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    index, doc_mapping = load_vector_db()
    q_vec = embedder.encode([query])
    D, I = index.search(q_vec, k)
    return [doc_mapping[i] for i in I[0]]

# ---------- Query Gemma 4:e4b ----------
def ask_gemma(context, query):
    system_prompt = f"""
You are a legal research assistant. Use the context below to answer the query accurately.

Context:
{context}

Query:
{query}

Rules:
- Answer strictly based on context
- Cite relevant cases, statutes
- Summarize clearly
- Do not hallucinate
"""
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": system_prompt}]
        )
        return response['message']['content']
    except Exception as e:
        return f"[LLM ERROR] {str(e)}"

# ---------- Streamlit UI ----------
st.title("Local Legal Research AI Agent")

st.sidebar.header("Document Management")
uploaded_file = st.sidebar.file_uploader("Upload a legal document", type=["pdf","docx","txt"])
if uploaded_file is not None:
    save_path = os.path.join(DOCUMENTS_PATH, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"Saved {uploaded_file.name}")
    build_vector_db()

if not os.path.exists(VECTOR_DB_FILE):
    st.warning("No vector DB found. Upload documents to build the database.")
else:
    st.success("Vector DB ready.")

st.header("Ask a Legal Question")
query = st.text_area("Enter your legal query:")

if st.button("Get Answer"):
    if not query.strip():
        st.error("Please enter a query.")
    else:
        sanitized_query = regex_redact(query)
        top_docs = retrieve(sanitized_query, k=3)
        context = "\n---\n".join(top_docs)
        answer = ask_gemma(context, sanitized_query)
        st.subheader("Sanitized Answer")
        st.write(answer)