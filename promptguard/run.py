import ollama
import re

def regex_redact(text):
    text = re.sub(r'\b\d{9}[VvXx]\b', '[REDACTED_NIC]', text)
    text = re.sub(r'[\w\.-]+@[\w\.-]+', '[REDACTED_EMAIL]', text)
    text = re.sub(r'\b\d{10}\b', '[REDACTED_PHONE]', text)
    return text

def sanitize_prompt(prompt: str) -> str:
    if not prompt.strip():
        return "[EMPTY PROMPT]"

    partially_redacted = regex_redact(prompt)

    system_prompt = f"""
You are PromptGuard, a privacy-preserving AI firewall.

Redact sensitive information while preserving readability.

Text:
{partially_redacted}
"""
    try:
        response = ollama.chat(
            model="gemma4:e4b",
            messages=[{"role": "user", "content": system_prompt}]
        )
        return response['message']['content']
    except Exception as e:
        print("Ollama error:", e)
        return "[SANITIZATION FAILED]"

if __name__ == "__main__":
    while True:
        user_input = input("Enter prompt (or 'exit' to quit): ")
        if user_input.lower() == "exit":
            break
        sanitized = sanitize_prompt(user_input)
        print("Sanitized Output:\n", sanitized)