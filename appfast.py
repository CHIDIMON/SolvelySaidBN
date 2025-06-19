import os
import io
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from chatapi import init_chat, chat_with_text
from whisperapi import transcribe_audio_api

from db import (
    initialize_database,
    get_all_menus,
    get_menu_image,
)
initialize_database()

load_dotenv()
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "default123")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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

        if path.startswith(("/ping", "/upload", "/chat", "/image")):
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif path.startswith("/login") and origin == "https://solvelysaid.space":
            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        return response

app.add_middleware(CustomCORSMiddleware)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        image_data = get_menu_image(menu_name)
        if image_data:
            return StreamingResponse(io.BytesIO(image_data), media_type="image/jpeg")
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

        all_menus = [menu["name"] for menu in get_all_menus()]

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
        menus = get_all_menus()
        return {"menus": menus}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("page.html", {"request": request})

init_chat()
initialize_database()