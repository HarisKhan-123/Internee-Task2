# AI Resume Feedback Tool

A small Flask web app that analyzes an uploaded resume (PDF or DOCX) and
returns AI-generated feedback on **structure**, **skills**, and **content**,
plus concrete improvement suggestions.

Uses **Groq's free-tier API** (Llama 3.3 70B) instead of the paid OpenAI API.

## Features
- Upload a resume as PDF or DOCX
- Text extraction with `pypdf` and `python-docx`
- LLM analysis via Groq (free, fast inference)
- Scored feedback: overall score + structure/skills/content sub-scores
- Strengths, improvement areas, missing sections, ATS notes
- Simple drag-and-drop web UI, no database required
- Uploaded files are deleted immediately after analysis

## 1. Get a free Groq API key
1. Go to https://console.groq.com/keys
2. Sign up (free) and create an API key
3. Groq's free tier gives generous rate limits — no credit card, no OpenAI cost

## 2. Setup

```bash
cd resume-feedback-tool

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# then edit .env and paste your GROQ_API_KEY
```

## 3. Run

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Project structure

```
resume-feedback-tool/
├── app.py                 # Flask routes: upload form + analysis endpoint
├── requirements.txt
├── .env.example
├── utils/
│   ├── parser.py           # PDF/DOCX text extraction
│   └── analyzer.py         # Groq API call + JSON-structured feedback
├── templates/
│   ├── base.html
│   ├── index.html          # Upload page
│   └── results.html        # Feedback report page
├── static/
│   └── style.css
└── uploads/                # Temp storage, files deleted after each request
```

## How it works
1. User uploads a PDF/DOCX on the home page.
2. `utils/parser.py` extracts raw text (`pypdf` for PDFs, `python-docx` for Word files).
3. `utils/analyzer.py` sends that text to Groq's chat-completions endpoint with a
   system prompt that forces a structured JSON response (score, strengths,
   weaknesses, ATS notes, etc.).
4. `app.py` renders `results.html` with the parsed JSON feedback.
5. The uploaded file is deleted right after processing — nothing is stored.

## Customizing
- **Change the model**: set `GROQ_MODEL` in `.env` (see available models at
  https://console.groq.com/docs/models — e.g. `llama-3.1-8b-instant` for an
  even faster/cheaper option, or `llama-3.3-70b-versatile` for higher quality).
- **Change the feedback shape**: edit the JSON schema described in the
  `SYSTEM_PROMPT` inside `utils/analyzer.py`, then update `results.html` to
  match.
- **File size limit**: `MAX_CONTENT_LENGTH` in `app.py` (default 8 MB).

## Deploying
This is a standard Flask app — deploy it anywhere that runs Python (Render,
Railway, Fly.io, a VPS with gunicorn, etc.). For production:
- Set `FLASK_DEBUG=0`
- Run behind a real WSGI server, e.g. `gunicorn app:app`
- Set a strong random `FLASK_SECRET_KEY`
- Keep `GROQ_API_KEY` as a server-side environment variable — never expose it
  to the browser

## Notes on the "free alternative" requirement
The original task suggested OpenAI + LangChain. This implementation swaps in
**Groq** directly (its Python SDK is a lightweight, OpenAI-compatible client)
since Groq offers a genuinely free tier with fast Llama-model inference and
no LangChain overhead is needed for a single-call, structured-JSON use case
like this one. If you'd like a LangChain-wrapped version instead (e.g. to add
multi-step chains or memory later), Groq is also usable as a LangChain LLM
provider via `langchain-groq` — ask and I can convert it.
