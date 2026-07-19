import warnings
warnings.filterwarnings("ignore")

import os
import chromadb
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv()

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────
app = Flask(__name__)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
chroma_client = chromadb.PersistentClient(path="./notes_db")
collection = chroma_client.get_or_create_collection(name="physics_notes")


# ─────────────────────────────────────────────
# CORE FUNCTIONS (same logic as terminal app)
# ─────────────────────────────────────────────

def add_notes_to_db(text):
    """Split text into chunks and store in ChromaDB"""
    chunks = [
        line.strip()
        for line in text.split("\n")
        if len(line.strip()) > 20
    ]

    if not chunks:
        return 0

    start_id = collection.count()
    ids = [f"note_{start_id + i}" for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids)
    return len(chunks)


def search_notes(query):
    """Search ChromaDB for relevant notes"""
    total = collection.count()
    if total == 0:
        return []
    n = min(4, total)
    results = collection.query(query_texts=[query], n_results=n)
    return results["documents"][0]


def search_web(query):
    """Search DuckDuckGo"""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(f"{query} physics", max_results=3):
                results.append({
                    "title"  : r["title"],
                    "snippet": r["body"],
                    "url"    : r["href"]
                })
        return results
    except:
        return []


def get_answer(question):
    """
    Full RAG pipeline:
    1. Search notes
    2. Search web if notes not enough
    3. Combine and answer
    Returns: answer text, notes used, web sources used
    """

    # Search notes
    relevant_notes = search_notes(question)
    notes_context  = ""
    if relevant_notes:
        notes_context = "\n".join([
            f"Note {i+1}: {note}"
            for i, note in enumerate(relevant_notes)
        ])

    # Search web
    web_results  = search_web(question)
    web_context  = ""
    web_sources  = []
    if web_results:
        web_context = "\n".join([
            f"Web {i+1}: {r['title']} — {r['snippet']}"
            for i, r in enumerate(web_results)
        ])
        web_sources = [
            {"title": r["title"], "url": r["url"]}
            for r in web_results
        ]

    # Build combined context
    combined = ""
    if notes_context:
        combined += f"FROM YOUR NOTES:\n{notes_context}\n\n"
    if web_context:
        combined += f"FROM WEB:\n{web_context}"

    if not combined:
        combined = "No information found."

    # Ask Groq
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an expert Physics tutor.
                Answer using the provided sources.
                Prioritise the student's own notes.
                Use web results to add more detail.
                Format your answer clearly with bullet points
                where appropriate.
                At the end mention if answer came from
                notes, web, or both."""
            },
            {
                "role": "user",
                "content": f"Sources:\n{combined}\n\nQuestion: {question}"
            }
        ],
        temperature=0.3,
        max_tokens=1024
    )

    answer = response.choices[0].message.content
    return answer, relevant_notes, web_sources


# ─────────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    """Main page — show the chat interface"""
    return render_template("index.html",
                           notes_count=collection.count())


@app.route("/ask", methods=["POST"])
def ask():
    """
    Receives question from browser
    Returns answer as JSON
    """
    data     = request.get_json()
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Please type a question."})

    answer, notes_used, web_sources = get_answer(question)

    return jsonify({
        "answer"     : answer,
        "notes_used" : notes_used,
        "web_sources": web_sources
    })


@app.route("/add-notes", methods=["POST"])
def add_notes():
    """
    Receives notes text from browser
    Stores in ChromaDB
    Returns how many chunks were added
    """
    data  = request.get_json()
    text  = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No notes provided."})

    count = add_notes_to_db(text)

    return jsonify({
        "message"    : f"✅ Added {count} notes to database!",
        "total_notes": collection.count()
    })


@app.route("/notes-count")
def notes_count():
    """Returns current note count"""
    return jsonify({"count": collection.count()})


if __name__ == "__main__":
    app.run(debug=True)