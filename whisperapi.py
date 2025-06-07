import requests

GROQ_API_KEY = "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"
def transcribe_audio_api(file_path, language="th"):
    """
    ถอดเสียงจากไฟล์เสียงด้วย Faster-Whisper และคืนข้อความที่ได้
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