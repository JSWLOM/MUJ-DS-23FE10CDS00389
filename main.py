import io, json, os, time
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from groq import Groq
from pypdf import PdfReader

load_dotenv()
cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
prompts = yaml.safe_load(open("prompts.yaml", encoding="utf-8"))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
app = FastAPI()


def extract_text(file: UploadFile, data: bytes) -> str:
    if file.filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    return data.decode("utf-8", errors="ignore")


def call_llm(resume: str, jd: str) -> dict:
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
            if attempt == cfg["max_retries"] - 1:
                raise HTTPException(502, f"LLM call failed: {e}")
            time.sleep(2 ** attempt)


@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    jd_text: str = Form(""),
    jd_file: UploadFile | None = File(None),
):
    resume_text = extract_text(resume, await resume.read()).strip()
    if len(resume_text) < 50:
        raise HTTPException(400, "Could not read enough text from the resume. Scanned/image PDFs are not supported, try a text-based PDF.")

    if jd_file and jd_file.filename:
        jd = extract_text(jd_file, await jd_file.read()).strip()
    else:
        jd = jd_text.strip()
    if len(jd) < 30:
        raise HTTPException(400, "The job description is too short or could not be read.")

    limit = cfg["max_resume_chars"]
    return call_llm(resume_text[:limit], jd[:limit])


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")