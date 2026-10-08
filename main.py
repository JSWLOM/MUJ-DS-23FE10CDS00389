import io
import json
import os
import time
import traceback
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from groq import Groq
from pypdf import PdfReader

load_dotenv()

BASE_DIR = Path(__file__).parent
cfg = yaml.safe_load(open(BASE_DIR / "config.yaml", encoding="utf-8"))
prompts = yaml.safe_load(open(BASE_DIR / "prompts.yaml", encoding="utf-8"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
app = FastAPI(title="NLP Based Resume Analyzer")


def extract_text(file: UploadFile, data: bytes) -> str:
    """Extract plain text from an uploaded PDF or TXT file."""
    name = (file.filename or "").lower()
    if name.endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            raise HTTPException(400, f"Could not read '{file.filename}'. Please upload a valid PDF.")
    return data.decode("utf-8", errors="ignore")


def call_llm(resume: str, jd: str) -> dict:
    """Send the resume + JD to Groq and return the parsed JSON result."""
    user_prompt = prompts["user"].replace("{resume}", resume).replace("{jd}", jd)

    for attempt in range(cfg["max_retries"]):
        try:
            res = client.chat.completions.create(
                model=cfg["model"],
                temperature=cfg["temperature"],
                max_tokens=cfg["max_tokens"],
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompts["system"]},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return json.loads(res.choices[0].message.content)
        except Exception as e:
            traceback.print_exc()  # shows the real error in the terminal / Vercel logs
            if attempt == cfg["max_retries"] - 1:
                raise HTTPException(502, f"LLM call failed: {e}")
            time.sleep(2 ** attempt)


@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    jd_text: str = Form(""),
    jd_file: UploadFile | None = File(None),
):
    # 1. Resume
    resume_text = extract_text(resume, await resume.read()).strip()
    if len(resume_text) < 50:
        raise HTTPException(
            400,
            "Could not read enough text from the resume. "
            "Scanned/image PDFs are not supported, try a text-based PDF.",
        )

    # 2. Job description: uploaded file takes priority, otherwise pasted text
    if jd_file and jd_file.filename:
        jd = extract_text(jd_file, await jd_file.read()).strip()
    else:
        jd = jd_text.strip()
    if len(jd) < 30:
        raise HTTPException(400, "The job description is too short or could not be read.")

    # 3. LLM analysis
    limit = cfg["max_resume_chars"]
    return call_llm(resume_text[:limit], jd[:limit])


# Local only: on Vercel, files in public/ are served by the CDN automatically.
# Keep this mount as the LAST statement so it doesn't shadow the /analyze route.
if not os.getenv("VERCEL"):
    app.mount("/", StaticFiles(directory=BASE_DIR / "public", html=True), name="public")