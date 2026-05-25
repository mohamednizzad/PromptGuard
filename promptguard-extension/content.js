console.log("PromptGuard active");

async function sanitizePrompt() {
    // Detect input box (contenteditable or textarea)
    const inputBoxes = document.querySelectorAll('[contenteditable="true"], textarea');
    let inputBox = null;

    for (let box of inputBoxes) {
        if ((box.innerText && box.innerText.length > 0) || (box.value && box.value.length > 0)) {
            inputBox = box;
            break;
        }
    }
    inputBox = inputBox || inputBoxes[inputBoxes.length - 1];

    if (!inputBox) {
        alert("No prompt input found");
        return;
    }

    // Small delay for dynamic UI
    await new Promise(r => setTimeout(r, 50));

    const originalPrompt = inputBox.value || inputBox.innerText || inputBox.textContent;
    console.log("PROMPT:", originalPrompt);

    if (!originalPrompt || !originalPrompt.trim()) {
        alert("Prompt is empty");
        return;
    }

    try {
        // Call local FastAPI backend
        const response = await fetch(
            "http://127.0.0.1:8000/scan",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: originalPrompt })
            }
        );

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        if (data.error) {
            console.error("Backend returned error:", data.error);
            alert(`Sanitize failed: ${data.error}`);
            return;
        }

        console.log("SANITIZED:", data.safe_prompt);

        // Replace prompt in input box
        if (inputBox.value !== undefined) {
            inputBox.value = data.safe_prompt;
        } else {
            inputBox.innerText = data.safe_prompt;
        }

        inputBox.dispatchEvent(new Event('input', { bubbles: true }));
        alert("Prompt sanitized successfully");

    } catch (err) {
        console.error("Sanitize fetch error:", err);
        alert(`Backend connection failed: ${err.message}`);
    }
}

function createButton() {
    if (document.getElementById("promptguard-btn")) return;

    const button = document.createElement("button");
    button.id = "promptguard-btn";
    button.innerText = "Sanitize Prompt";

    button.style.position = "fixed";
    button.style.bottom = "20px";
    button.style.right = "20px";
    button.style.zIndex = "999999";
    button.style.padding = "12px 18px";
    button.style.background = "#10a37f";
    button.style.color = "white";
    button.style.border = "none";
    button.style.borderRadius = "10px";
    button.style.fontSize = "14px";
    button.style.cursor = "pointer";
    button.style.boxShadow = "0 2px 10px rgba(0,0,0,0.2)";
    button.onclick = sanitizePrompt;

    document.body.appendChild(button);
    console.log("Sanitize button added");
}

// Keep adding the button if the page reloads dynamic UI
setInterval(createButton, 2000);