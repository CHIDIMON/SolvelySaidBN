import os
import io
import traceback
import sqlite3
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

from chatapi import init_chat, chat_with_text
from whisperapi import transcribe_audio_api

# โหลดค่า .env
load_dotenv()
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "default123")

# ---------- สร้าง FastAPI app ----------
app = FastAPI()

# ---------- Custom CORS Middleware แบบแยก route ----------
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        if request.method == "OPTIONS":
            return Response(status_code=204, headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "*"
            })

        response = await call_next(request)
        path = request.url.path
        origin = request.headers.get("origin", "")

        # ✅ เพิ่มให้แน่ใจว่า /ping /upload /chat ได้ Header
        if path.startswith(("/ping", "/upload", "/chat", "/image")):
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif path.startswith("/login") and origin == "https://solvelysaid.space":
            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        return response

# ---------- เพิ่ม Middleware ----------
app.add_middleware(CustomCORSMiddleware)

# ---------- โฟลเดอร์อัปโหลด ----------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- เชื่อมฐานข้อมูล ----------
def get_db_connection():
    conn = sqlite3.connect('food_menu.db')
    conn.row_factory = sqlite3.Row
    return conn

# ---------- ENDPOINTS ----------

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    password = data.get("password", "")
    if password == LOGIN_PASSWORD:
        return {"success": True}
    return JSONResponse(content={"success": False}, status_code=401)

@app.get("/ping")
async def ping():
    return "pong"

@app.get("/image/{menu_name}")
async def get_image(menu_name: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM menu WHERE name=?", (menu_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return StreamingResponse(io.BytesIO(row["image"]), media_type="image/jpeg")
        return JSONResponse(content={"error": "ไม่พบรูปภาพ"}, status_code=404)
    except Exception as e:
        print("🔥 ERROR:", str(e))
        return JSONResponse(content={"error": "เกิดข้อผิดพลาดในการดึงรูปภาพ"}, status_code=500)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), language: str = Form("th")):
    if not file.filename:
        return JSONResponse(content={"error": "ไม่ได้เลือกไฟล์"}, status_code=400)

    temp_path: str | None = None

    try:
        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        text = transcribe_audio_api(temp_path, language=language)
        chat_response = chat_with_text(text, lang_code=language)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM menu")
        all_menus = [row['name'] for row in cursor.fetchall()]
        conn.close()

        matched_menu = next((menu for menu in all_menus if menu.lower() in text.lower()), None)

        result = {
            "text": text,
            "chat_response": chat_response
        }
        if matched_menu:
            result["menu"] = matched_menu

        return result

    except Exception:
        print("🔥 ERROR:", traceback.format_exc())
        return JSONResponse(content={"error": "เกิดข้อผิดพลาดในการประมวลผล"}, status_code=500)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        data = await request.json()
        user_input = data.get("text", "")
        lang_code = data.get("language", "th")

        if not user_input:
            return JSONResponse(content={"error": "ไม่มีข้อความ"}, status_code=400)

        response = chat_with_text(user_input, lang_code=lang_code)
        return {"response": response}
    except Exception as e:
        print("🔥 ERROR:", str(e))
        return JSONResponse(content={"error": "เกิดข้อผิดพลาดในการสนทนา"}, status_code=500)

@app.get("/debug/menus")
async def debug_menus():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM menu")
        menus = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
        conn.close()
        return {"menus": menus}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/", response_class=HTMLResponse)
async def home():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Welcome to solvelysaid.space</title>
      <link rel="icon" type="image/png" href="solvely.png" />
      <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600&display=swap" rel="stylesheet">
      <style>
        body {
          margin: 0;
          background: #000;
          color: white;
          font-family: 'Orbitron', sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
          text-align: center;
          padding: 0 20px;
          box-sizing: border-box;
        }
        .container {
          width: 100%;
          max-width: 960px;
        }
        h1 {
          font-size: 3rem;
          letter-spacing: 2px;
          margin-bottom: 20px;
          line-height: 1.3;
        }
        p {
          font-size: 1.2rem;
          color: #aaaaaa;
          margin-bottom: 16px;
        }
        a {
          display: inline-block;
          text-decoration: none;
          color: black;
          background: white;
          padding: 14px 30px;
          font-weight: bold;
          border-radius: 8px;
          font-size: 1rem;
          transition: background 0.3s ease, transform 0.2s ease;
        }
        a:hover {
          background: #00e5ff;
          transform: scale(1.05);
        }
        .highlight {
          color: #00e5ff;
        }
        @media (max-width: 768px) {
          h1 {
            font-size: 2rem;
            line-height: 1.3;
          }
          p {
            font-size: 1rem;
          }
          a {
            padding: 10px 22px;
            font-size: 0.95rem;
          }
          .container {
            max-width: 90%;
          }
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Welcome to<br><span class="highlight">solvelysaid.space</span></h1>
        <p>Mission: Backend API is running</p>
        <p><b>Thirasak.official</b></p>
        <a href="https://solvelysaid.space/">ENTER TO MAIN</a>
      </div>
    </body>
    </html>
    '''

# ---------- สร้างฐานข้อมูลเมนูเริ่มต้น ----------
def initialize_database():
    conn = sqlite3.connect('food_menu.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image BLOB
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        with open("image/Pizza.webp", "rb") as f:
            pizza_img = f.read()
        cursor.execute("INSERT INTO menu (name, image) VALUES (?, ?)", ("Pizza", pizza_img))
        with open("image/Tomyum.jpg", "rb") as f:
            tomyum_img = f.read()
        cursor.execute("INSERT INTO menu (name, image) VALUES (?, ?)", ("ต้มยำ", tomyum_img))
        cursor.execute("INSERT INTO menu (name, image) VALUES (?, ?)", ("Tom Yum", tomyum_img))
        cursor.execute("INSERT INTO menu (name, image) VALUES (?, ?)", ("Tom Yam", tomyum_img))
    conn.commit()
    conn.close()

# ---------- เรียกตอนเริ่มแอป ----------
init_chat()
initialize_database()
