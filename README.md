# NLP Based Resume Analyzer

*(Resume × JD Matcher)*

## Student Details

| Field | Details |
|---|---|
| **Name** | Om Jaiswal |
| **Registration Number** | 23FE10CDS00389 |
| **Branch** | B.Tech Computer Science (Data Science Engineering) |
| **University** | Manipal University Jaipur |
| **Batch** | F |
| **Project Title** | NLP Based Resume Analyzer |
| **GitHub Username** | [jswlom](https://github.com/jswlom) |
| **Training Program** | *[Add training program name, duration and trainer/organization here]* |

---

## Overview

An NLP project that uses a Large Language Model (via the **Groq API**) to compare a resume against a job description. It returns a match score, matched and missing skills, strengths, actionable resume improvements, and a tailored professional summary, all as structured JSON rendered in a clean web interface.

> Solo NLP course project submission.

---

## Features

- Upload a resume as **PDF or TXT**
- Provide the job description as **pasted text or an uploaded PDF/TXT**
- LLM-powered analysis returning a strict JSON schema:
  - Match score (0 to 100)
  - Overall summary
  - Matched skills and missing skills
  - Strengths grounded in the resume
  - Specific, section-wise improvement suggestions
  - A rewritten professional summary tailored to the job
- Prompts and settings live in separate files (`prompts.yaml`, `config.yaml`), so nothing is hard-coded
- Automatic retries with exponential backoff on API failures
- Input validation and clear error messages in the UI
- Black, white and orange interface with drag-and-drop uploads and small animations (plain HTML, CSS and JS)

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM provider | Groq API (model set in `config.yaml`) |
| Backend | Python, FastAPI, Uvicorn |
| PDF parsing | pypdf |
| Config / prompts | YAML, python-dotenv |
| Frontend | HTML, CSS, vanilla JavaScript |

---

## How It Works

```
Browser (HTML/CSS/JS)
   │  resume file + JD (text or file)
   ▼
FastAPI  POST /analyze
   │  1. validate inputs
   │  2. extract text from PDF/TXT (pypdf)
   │  3. build prompt from prompts.yaml
   ▼
Groq LLM API  (JSON mode, low temperature, retries)
   │  structured JSON response
   ▼
Browser renders score ring, skill chips, strengths,
improvements and tailored summary
```

The API key is stored only on the server (`.env`). The frontend never sees it.

---

## Project Structure

```
resume-matcher/
├── main.py              # FastAPI app: file parsing, LLM call, retries
├── prompts.yaml         # System prompt + user prompt template
├── config.yaml          # Model name, temperature, token limits, retries
├── .env.example         # Template for the API key
├── requirements.txt     # Python dependencies
├── README.md
└── frontend/
    ├── index.html       # UI structure
    ├── style.css        # Theme and animations
    └── script.js        # Uploads, API call, rendering
```

---

## Setup and Run

### 1. Clone the repository
```bash
git clone <your-repo-link>
cd resume-matcher
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key
Get a free key from [console.groq.com](https://console.groq.com), then copy the template and fill it in:
```bash
cp .env.example .env      # on Windows: copy .env.example .env
```
Edit `.env`:
```
GROQ_API_KEY=your_key_here
```
(no quotes, no spaces)

### 5. Start the server
```bash
uvicorn main:app --reload
```

### 6. Open the app
Go to **http://127.0.0.1:8000**

---

## Usage

1. Upload your resume (PDF or TXT).
2. Choose **Paste text** or **Upload PDF** for the job description.
3. Click **Analyze match**.
4. Review the score, skill gaps, strengths, suggestions and tailored summary.

---

## Configuration (`config.yaml`)

| Key | Purpose |
|---|---|
| `model` | Groq model ID used for analysis |
| `temperature` | Low value (0.2) for consistent, repeatable scoring |
| `max_tokens` | Upper limit for the response (includes reasoning tokens) |
| `max_retries` | Number of attempts for a failed API call |
| `max_resume_chars` | Input length cap to stay within model limits |

If the model is ever retired by the provider, change `model` here. No code change is needed.

---

## Prompt Design (`prompts.yaml`)

- **Role prompting:** the system prompt sets the model up as a technical recruiter and ATS analyst.
- **Grounding rules:** only skills actually written in the resume may be listed as matched, and the model must not invent experience, publications or awards.
- **"X or Y" handling:** if the JD accepts alternatives (e.g. TensorFlow *or* PyTorch), the requirement counts as met when any one is present.
- **Rubric-based scoring:** required skills 50%, relevant experience 30%, education and keywords 20%.
- **Strict output schema:** the model must return JSON in a defined structure, which the frontend renders directly.
- **Few-shot example:** one example of a good improvement suggestion sets the expected level of specificity.

---

## API Reference

### `POST /analyze`

`multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `resume` | file | Resume (PDF or TXT) |
| `jd_text` | string | Job description text (optional if `jd_file` is given) |
| `jd_file` | file | Job description file (optional if `jd_text` is given) |

**Response (200):**
```json
{
  "match_score": 70,
  "summary": "...",
  "matched_skills": ["Python", "FastAPI"],
  "missing_skills": ["Scikit-learn"],
  "strengths": ["..."],
  "improvements": [{"section": "Projects", "suggestion": "..."}],
  "rewritten_summary": "..."
}
```

**Errors:** `400` for unreadable or too-short input, `502` if the LLM call fails after all retries.

---

## Error Handling

- Resume or JD missing, too short, or unreadable (e.g. scanned image PDFs) returns a clear message in the UI
- LLM failures are retried up to `max_retries` times with exponential backoff (1s, then 2s) before returning an error
- The model output is parsed as JSON, and malformed responses trigger a retry

---

## Limitations

- Scanned or image-only PDFs are not supported (no OCR)
- Very long documents are truncated to `max_resume_chars`
- The match score is an LLM estimate based on the rubric in the prompt, so treat it as guidance, not a guarantee

## Future Improvements

- OCR support for scanned PDFs
- Export the analysis as a PDF report
- Compare one resume against multiple job descriptions at once
- Streamed responses for faster perceived output

---

## Author

**Om Jaiswal** | Reg. No. 23FE10CDS00389 | B.Tech CSE (Data Science Engineering), Batch F, Manipal University Jaipur
GitHub: [@jswlom](https://github.com/jswlom)

NLP course project submission: *NLP Based Resume Analyzer*.
