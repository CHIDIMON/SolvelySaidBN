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

from fastapi.middleware.cors import CORSMiddleware  # <-- เพิ่ม CORS Middleware

from chatapi import init_chat, chat_with_text
from whisperapi import transcribe_audio_api

from db import (
    initialize_database,
    get_all_menus,
    get_menu_image_thumb,
    get_menu_image_720p,
    insert_menu,
    update_menu,
    delete_menu,
)

initialize_database()

load_dotenv()
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "default123")

app = FastAPI()

# == ใส่ CORS Middleware ของ FastAPI ตรงนี้เลย ==
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ถ้าต้องการจำกัด origin ให้ใส่ domain ที่อนุญาต
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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

@app.get("/image/thumb/{menu_name}")
async def get_image_thumb(menu_name: str):
    try:
        image_data = get_menu_image_thumb(menu_name)
        if image_data:
            return StreamingResponse(io.BytesIO(image_data), media_type="image/jpeg")
        return JSONResponse(content={"error": "ไม่พบรูปภาพ"}, status_code=404)
    except Exception as e:
        print("🔥 ERROR:", str(e))
        return JSONResponse(content={"error": "เกิดข้อผิดพลาดในการดึงรูปภาพ"}, status_code=500)

@app.get("/image/720p/{menu_name}")
async def get_image_720p(menu_name: str):
    try:
        image_data = get_menu_image_720p(menu_name)
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

# ==== CRUD เมนู ====

@app.post("/menu/add")
async def add_menu(request: Request):
    data = await request.json()
    name = data.get("name")
    price = data.get("price", 0)
    desc = data.get("description", "")
    if not name:
        return JSONResponse(content={"error": "ต้องใส่ชื่อเมนู"}, status_code=400)
    insert_menu(name=name, price=price, description=desc)
    return {"success": True}

@app.post("/menu/edit")
async def edit_menu(request: Request):
    data = await request.json()
    menu_id = data.get("id")
    name = data.get("name")
    price = data.get("price")
    desc = data.get("description")
    if not menu_id:
        return JSONResponse(content={"error": "ต้องระบุ id เมนู"}, status_code=400)
    update_menu(menu_id, name=name, price=price, description=desc)
    return {"success": True}

@app.post("/menu/delete")
async def delete_menu_api(request: Request):
    data = await request.json()
    menu_id = data.get("id")
    if not menu_id:
        return JSONResponse(content={"error": "ต้องระบุ id เมนู"}, status_code=400)
    delete_menu(menu_id)
    return {"success": True}

@app.post("/menu/edit/batch")
async def edit_menu_batch(request: Request):
    data = await request.json()
    menus = data.get("menus", [])
    for menu in menus:
        menu_id = menu.get("id")
        name = menu.get("name")
        price = menu.get("price")
        desc = menu.get("description")
        if menu_id:
            update_menu(menu_id, name=name, price=price, description=desc)
    return {"success": True}
# ==== END CRUD ====

init_chat()
initialize_database()
