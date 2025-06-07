# whisper.py
from faster_whisper import WhisperModel

# โหลดโมเดลเมื่อ import
print("⏳ กำลังโหลดโมเดล Faster-Whisper...")
model = WhisperModel("large-v3", compute_type="int8")
print("✅ โหลดโมเดลเสร็จสิ้น")

def transcribe_audio(file_path, language="th"):
    """
    ถอดเสียงจากไฟล์เสียงด้วย Faster-Whisper และคืนข้อความที่ได้
    """
    segments, info = model.transcribe(
        file_path,
        language=language,
        temperature=0,
        beam_size=5,
        best_of=5
    )
    text = " ".join([seg.text for seg in segments]).strip()
    return text
