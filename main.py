from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse
from pypdf import PdfReader
import requests
import os
import io
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

app = FastAPI()

# Get values from environment
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")


# ✅ Add middleware BEFORE anything else
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://pdf-loader.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root(request: Request):
    return FileResponse('index.html', media_type='text/html')


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    # Read PDF content
    pdf_bytes = await file.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    content = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            content += text + "\n"

    # Limit text length for Notion
    content = content[:2000]

    # Send to Notion
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": file.filename}}]},
            "Text": {"rich_text": [{"text": {"content": content}}]}
        }
    }
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return {"status": "success", "file": file.filename}
    else:
        return {
            "status": "failed",
            "error": response.text,
            "status_code": response.status_code
        }
