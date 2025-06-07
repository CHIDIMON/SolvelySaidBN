# whisperapi.py
import os
import requests
from dotenv import load_dotenv
load_dotenv()

# ✅ ดึง GROQ_API_KEY จาก Environment Variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def transcribe_audio_api(file_path, language="th"):
    """
    ถอดเสียงจากไฟล์เสียงด้วย Groq Whisper API
    """
    url = "https://api.groq.com/openai/v1/audio/transcriptions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    files = {
        "file": (file_path, open(file_path, "rb")),
        "model": (None, "whisper-large-v3"),
        "language": (None, language)
    }

    try:
        response = requests.post(url, headers=headers, files=files)
        response.raise_for_status()
        return response.json().get("text", "")
    except Exception as e:
        print(f"🔥 ERROR: {e}")
        return ""
