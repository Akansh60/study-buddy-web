// ── ADD NOTES ────────────────────────────────
async function addNotes() {
    const text    = document.getElementById("notes-input").value.trim()
    const btn     = document.getElementById("add-notes-btn")
    const message = document.getElementById("notes-message")

    if (!text) {
        showMessage(message, "Please paste some notes first.", "error")
        return
    }

    // disable button while saving
    btn.disabled    = true
    btn.textContent = "Saving..."

    try {
        const response = await fetch("/add-notes", {
            method : "POST",
            headers: { "Content-Type": "application/json" },
            body   : JSON.stringify({ text: text })
        })

        const data = await response.json()

        if (data.error) {
            showMessage(message, data.error, "error")
        } else {
            showMessage(message, data.message, "success")
            // update notes count in header
            document.getElementById("notes-count").textContent = data.total_notes
            // clear the textarea
            document.getElementById("notes-input").value = ""
        }

    } catch (error) {
        showMessage(message, "Something went wrong. Try again.", "error")
    }

    btn.disabled    = false
    btn.textContent = "💾 Save Notes"
}


// ── ASK QUESTION ─────────────────────────────
async function askQuestion() {
    const input    = document.getElementById("question-input")
    const question = input.value.trim()
    const chatBox  = document.getElementById("chat-box")

    if (!question) return

    // clear input
    input.value = ""

    // remove welcome message if present
    const welcome = chatBox.querySelector(".welcome-message")
    if (welcome) welcome.remove()

    // show user bubble
    addBubble(chatBox, question, "user-bubble")

    // show loading
    const loading = document.createElement("div")
    loading.className   = "loading-bubble"
    loading.textContent = "🤔 Searching notes and web..."
    chatBox.appendChild(loading)
    chatBox.scrollTop = chatBox.scrollHeight

    try {
        const response = await fetch("/ask", {
            method : "POST",
            headers: { "Content-Type": "application/json" },
            body   : JSON.stringify({ question: question })
        })

        const data = await response.json()

        // remove loading bubble
        loading.remove()

        if (data.error) {
            addBubble(chatBox, data.error, "bot-bubble")
        } else {
            // show answer bubble
            const bubble = addBubble(chatBox, data.answer, "bot-bubble")

            // show web sources if any
            if (data.web_sources && data.web_sources.length > 0) {
                const sourcesDiv = document.createElement("div")
                sourcesDiv.className = "sources-box"
                sourcesDiv.innerHTML = "<strong>🌐 Web Sources:</strong>"

                data.web_sources.forEach(source => {
                    sourcesDiv.innerHTML += `
                        <a href="${source.url}" target="_blank">
                            → ${source.title}
                        </a>`
                })
                bubble.appendChild(sourcesDiv)
            }

            // show notes used count
            if (data.notes_used && data.notes_used.length > 0) {
                const notesInfo = document.createElement("div")
                notesInfo.style.cssText = "margin-top:8px; font-size:0.8rem; color:#555;"
                notesInfo.textContent   = `📚 Used ${data.notes_used.length} chunks from your notes`
                bubble.appendChild(notesInfo)
            }
        }

    } catch (error) {
        loading.remove()
        addBubble(chatBox, "Something went wrong. Please try again.", "bot-bubble")
    }

    chatBox.scrollTop = chatBox.scrollHeight
}


// ── HELPER FUNCTIONS ─────────────────────────

function addBubble(chatBox, text, className) {
    const bubble = document.createElement("div")
    bubble.className   = `chat-bubble ${className}`
    bubble.textContent = text
    chatBox.appendChild(bubble)
    chatBox.scrollTop = chatBox.scrollHeight
    return bubble
}

function showMessage(element, text, type) {
    element.textContent = text
    element.className   = `message ${type}`
    // auto hide after 4 seconds
    setTimeout(() => { element.className = "message hidden" }, 4000)
}

// press Enter to submit question
function handleEnter(event) {
    if (event.key === "Enter") askQuestion()
}