# ⚡ Physics Study Buddy

An AI-powered physics tutor that answers questions
from your personal notes + web search.

## 🔗 Live Demo
[Click here to try it](web-production-eeaff.up.railway.app)

## ✨ Features
- Upload your physics notes (txt or plain text)
- Ask any physics question
- AI searches your notes first
- Falls back to web search if notes insufficient
- Powered by Groq + LLaMA + ChromaDB

## 🛠️ Built With
- Python + Flask
- Groq API (LLaMA 3.3)
- ChromaDB (vector database)
- DuckDuckGo Search
- Railway (deployment)

## 🚀 Run Locally
```bash
pip install -r requirements.txt
export GROQ_API_KEY="your-key"
python app.py
```