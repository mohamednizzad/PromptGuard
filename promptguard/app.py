async function sanitizePrompt() {
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

    await new Promise(r => setTimeout(r, 50));
    const originalPrompt = inputBox.value || inputBox.innerText || inputBox.textContent;

    if (!originalPrompt || !originalPrompt.trim()) {
        alert("Prompt is empty");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: originalPrompt })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        if (data.error) {
            alert(`Sanitize failed: ${data.error}`);
            return;
        }

        // Replace input with sanitized text
        if (inputBox.value !== undefined) inputBox.value = data.safe_prompt;
        else inputBox.innerText = data.safe_prompt;

        inputBox.dispatchEvent(new Event('input', { bubbles: true }));

        // --- AUTOMATIC SUBMIT ---
        // Create and dispatch Enter key event to submit the prompt
        const enterEvent = new KeyboardEvent('keydown', {
            key: 'Enter',
            code: 'Enter',
            keyCode: 13,
            which: 13,
            bubbles: true,
            cancelable: true
        });
        inputBox.dispatchEvent(enterEvent);

        console.log("Prompt sanitized and submitted automatically");

    } catch (err) {
        console.error("Sanitize fetch error:", err);
        alert(`Backend connection failed: ${err.message}`);
    }
}