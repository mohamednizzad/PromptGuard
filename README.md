# 🛡️ PromptGuard

**A local-first AI privacy firewall that sanitizes prompts before they reach the cloud.**

![Header Image](banner.png)

PromptGuard intercepts prompts typed into ChatGPT or Claude.ai, runs PII redaction using **Gemma 4:e4b** entirely on your machine, and replaces the raw prompt with a sanitized version — before anything leaves your device.

> Built for the [Gemma 4 Challenge]([https://dev.to/challenges/gemma4](https://dev.to/challenges/google-gemma-2026-05-06)) on DEV.to

---

## The Problem

Every day, professionals paste sensitive content into public AI interfaces:

- Legal documents with client NIC numbers and case details
- Medical records with patient health conditions
- Financial data with account information and salary details
- HR documents with employee personal data

This creates real legal exposure under **Sri Lanka's PDPA No. 9 of 2022**, **GDPR**, **UAE PDPL**, and equivalent frameworks. PromptGuard sits between your clipboard and the cloud — nothing sensitive gets transmitted.

---

## How It Works

```
You type a prompt with PII
        ↓
[PromptGuard Extension intercepts on click]
        ↓
POST → localhost:8000/scan
        ↓
Stage 1: Regex redaction (NIC, email, phone)
        ↓
Stage 2: Gemma 4:e4b contextual redaction (names, health, financial)
        ↓
Sanitized prompt returned
        ↓
Input box updated with clean version
        ↓
You submit → cloud AI never sees the original
```

---

## Repository Structure

```
promptguard-main/
│
├── promptguard/                  # Python backend
│   ├── main.py                   # FastAPI server (POST /scan endpoint)
│   ├── run.py                    # Redaction logic + CLI test harness
│   ├── agent.py                  # Legal RAG agent (Streamlit, optional)
│   ├── requirements.txt
│   ├── legal_docs/               # Drop legal PDFs/DOCX here for RAG agent
│   ├── vector_index.faiss        # Auto-generated vector index
│   └── doc_mapping.pkl           # Auto-generated document mapping
│
├── promptguard-extension/        # Chrome Extension (Manifest V3)
│   ├── manifest.json
│   ├── content.js                # Injection + sanitization logic
│   └── app.js                    # Auto-submit variant
│
└── README.md
```

---

## Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend runtime |
| [Ollama](https://ollama.ai) | Latest | Local LLM runtime |
| Gemma 4:e4b | via Ollama | PII redaction model |
| Chrome / Chromium | 88+ | Extension host |
| pip packages | see below | FastAPI, uvicorn, ollama |

---

## Installation

### 1. Install Ollama and pull Gemma 4:e4b

```bash
# Install Ollama from https://ollama.ai
# Then pull the model:
ollama pull gemma4:e4b
```

> **Why `e4b`?** The Mixture-of-Experts variant activates only relevant expert subnetworks per task, giving near-27B reasoning quality at local inference speeds. Tested against 2B, 4B, and 27B — `e4b` was the only variant that caught contextual PII while remaining fast enough for real-time prompt interception.

### 2. Set up the Python backend

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/promptguard.git
cd promptguard/promptguard

# Install dependencies
pip install fastapi uvicorn ollama pymupdf python-docx \
            sentence-transformers faiss-cpu streamlit

# Or using requirements.txt:
pip install -r requirements.txt
```

**`requirements.txt`:**
```
fastapi
uvicorn
ollama
pymupdf
python-docx
sentence-transformers
faiss-cpu
streamlit
```

### 3. Start the backend server

```bash
cd promptguard/
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Leave this running in the background.

### 4. Install the Chrome extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle, top right)
3. Click **Load unpacked**
4. Select the `promptguard-extension/` folder
5. The PromptGuard extension is now active

---

## Usage

### Via Chrome Extension (ChatGPT / Claude.ai)

1. Open [chatgpt.com](https://chatgpt.com) or [claude.ai](https://claude.ai)
2. Type or paste your prompt (including any sensitive content)
3. Click the **🛡️ Sanitize** button (bottom-right of the screen)
4. Wait 2–5 seconds for Gemma 4 to process
5. Your input box now contains the sanitized version
6. Submit as normal — the cloud AI never sees the original

### Via CLI (testing / development)

```bash
cd promptguard/
python run.py
```

```
Enter prompt (or 'exit' to quit): My client John Silva, NIC 912345678V, email john@gmail.com, called about his case.

Sanitized Output:
My client [REDACTED_NAME], NIC [REDACTED_NIC], email [REDACTED_EMAIL], called about his case.
```

### Via Legal RAG Agent (optional Streamlit UI)

```bash
cd promptguard/
streamlit run agent.py
```

Upload legal documents (PDFs, DOCX, TXT) via the sidebar. The agent builds a FAISS vector index and uses Gemma 4:e4b to answer legal queries — with all queries sanitized before retrieval.

---

## What Gets Redacted

### Stage 1 — Regex (instant)

| Pattern | Example | Replacement |
|---|---|---|
| Sri Lanka NIC | `999995678V` | `[REDACTED_NIC]` |
| Email | `user@gmail.com` | `[REDACTED_EMAIL]` |
| 10-digit phone | `0777654321` | `[REDACTED_PHONE]` |

### Stage 2 — Gemma 4:e4b (contextual)

| PII Type | Example | Replacement |
|---|---|---|
| Full names | `John Doe` | `[REDACTED_NAME]` |
| Health conditions | `HIV positive` | `[REDACTED_HEALTH]` |
| Financial details | `Rs. 2.4M salary` | `[REDACTED_FINANCIAL]` |
| Organization names | `ABCXYZ Hospital` | `[REDACTED_ORG]` |
| Temporal markers | `March 2024 admission` | `[REDACTED_TIMEFRAME]` |
| Implied references | `my usual number` | `[REDACTED_REFERENCE]` |

---

## Example Transformation

**Raw prompt:**
```
My client John Doe, NIC 999995678V, reached out via 
john.doe@example.com about a data breach at ABCXYZ Pvt Ltd. 
Her phone is 0777654321. The breach exposed her health records 
including her HIV status from the XYZABC Hospital 
admission in March 2024. Draft a letter to the Data Protection 
Authority under Section 23 of the PDPA.
```

**After Stage 1 (regex):**
```
My client John Doe, NIC [REDACTED_NIC], reached out via 
[REDACTED_EMAIL] about a data breach at XYZABC Hospital. 
Her phone is [REDACTED_PHONE]. The breach exposed her health records 
including her HIV status from the XYZABC Hospital 
admission in March 2024. Draft a letter to the Data Protection 
Authority under Section 23 of the PDPA.
```

**After Stage 2 (Gemma 4:e4b):**
```
My client [REDACTED_NAME], NIC [REDACTED_NIC], reached out via 
[REDACTED_EMAIL] about a data breach at [REDACTED_ORGANIZATION]. 
Her phone is [REDACTED_PHONE]. The breach exposed her health records 
including [REDACTED_HEALTH_CONDITION] from a hospital admission in 
[REDACTED_TIMEFRAME]. Draft a letter to the Data Protection Authority 
under Section 23 of the PDPA.
```

The AI receives a complete, actionable task. Your client's identity, health status, and organization are never transmitted.

---

## PDPA Alignment

This tool is designed with awareness of **Sri Lanka's Personal Data Protection Act No. 9 of 2022**:

| PDPA Provision | PromptGuard Response |
|---|---|
| **Section 7** — Data minimisation | Prompts are stripped to the minimum required for the AI task |
| **Section 10** — Technical measures | Local Gemma 4 redaction is the "appropriate technical measure" |
| **Schedule II** — Special categories | Health, genetic, biometric data are specifically targeted by Stage 2 |
| **Section 23** — Breach prevention | Preventing PII transmission to cloud reduces breach surface |
| **Section 38** — Penalty avoidance | Demonstrates due diligence for controllers using AI tools |

---

## Architecture

```
┌─────────────────────────────────────────┐
│             USER'S MACHINE               │
│                                         │
│  Chrome Extension          Backend       │
│  ┌─────────────┐          ┌──────────┐  │
│  │ content.js  │  POST    │FastAPI   │  │
│  │             ├─────────►│:8000/scan│  │
│  │ Injects btn │◄─────────┤          │  │
│  └─────────────┘  JSON    │  Regex   │  │
│                           │     +    │  │
│                           │ Gemma4   │  │
│                           │  :e4b    │  │
│                           └────┬─────┘  │
│                                │        │
│                     ┌──────────▼──────┐ │
│                     │ Ollama Runtime  │ │
│                     │ (local, no net) │ │
│                     └─────────────────┘ │
└─────────────────────────────────────────┘
             │ Only sanitized prompt
             ▼
     Cloud AI (ChatGPT / Claude)
```

---

## Known Limitations

- **Latency**: 2–5 seconds on mid-range hardware (M1 MacBook / 16GB RAM). Acceptable for sensitive document workflows.
- **False positives**: Gemma 4 may over-redact organization names that are public information. Domain-specific profiles are on the roadmap.
- **Backend must be running**: If Ollama or FastAPI isn't started, the extension fails. A health-check indicator is planned.
- **CSP restrictions**: Enterprise versions of ChatGPT or Claude may block content script injection.
- **English-primary**: Sinhala and Tamil name recognition is weaker than English. Fine-tuning on local PII patterns is a planned improvement.

---

## Roadmap

- [ ] `main.py` FastAPI server with proper error handling and health endpoint
- [ ] Diff view — show what changed before submission
- [ ] Domain profiles: `legal`, `medical`, `financial` redaction thresholds
- [ ] Firefox extension (Manifest V2)
- [ ] Backend health indicator in the extension popup
- [ ] Fine-tuned Gemma 4 on Sri Lankan PII patterns (NIC formats, Sinhala/Tamil names, address structures)
- [ ] Configurable auto-submit toggle

---

## Contributing

Pull requests are welcome. For significant changes, please open an issue first.

Areas where contributions would be most valuable:
- Additional regex patterns for other national ID formats (passport, driving licence)
- Improved system prompts for Gemma 4 in specific domains
- Firefox extension port
- Test suite for redaction accuracy

---

## License

MIT License — see `LICENSE` for details.

---

## Acknowledgements

- [Ollama](https://ollama.ai) — local LLM runtime
- [Google Gemma 4](https://ai.google.dev/gemma) — the model that makes local redaction feasible
- Sri Lanka PDPA No. 9 of 2022 — the legal framework this tool is designed to support
- [FastAPI](https://fastapi.tiangolo.com) — the backend framework
- [FAISS](https://github.com/facebookresearch/faiss) — vector search for the RAG agent

---

*Built as part of the [Gemma 4 Challenge](https://dev.to/challenges/gemma4) on DEV.to and check the Article [PromptGuard: I Built a Local AI Privacy Firewall That Sanitizes Your Prompts Before They Leave Your Machine]([https://dev.to/challenges/gemma4](https://dev.to/mohamednizzad/promptguard-i-built-a-local-ai-privacy-firewall-that-sanitizes-your-prompts-before-they-leave-pec))*
