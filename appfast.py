import os
import io
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

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
    add_order,
    get_orders,
    delete_order,
    delete_old_orders
)

initialize_database()
load_dotenv()
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "default123")

app = FastAPI()

allow_origins = [
    "https://solvelysaid.space",
    "https://app.solvelysaid.space",
    "https://solvelysaidbn.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
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

@app.post("/menu/add")
async def add_menu(
    name: str = Form(...),
    price: int = Form(0),
    description: str = Form(""),
    image: UploadFile = File(None)
):
    image_path = None
    if image and image.filename:
        save_path = os.path.join(UPLOAD_FOLDER, image.filename)
        with open(save_path, "wb") as f:
            f.write(await image.read())
        image_path = save_path
    insert_menu(name=name, price=price, description=description, image_path=image_path)
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

# ==== ORDER ====
@app.post("/order")
async def add_order_api(request: Request):
    data = await request.json()
    table_number = data.get("table_number")
    menus = data.get("menus")
    summary = data.get("summary")
    if not table_number or (not menus and not summary):
        return JSONResponse({"error": "ต้องระบุ table_number และเมนูหรือสรุป"}, status_code=400)
    add_order(table_number, menus or [], summary)
    return {"success": True}

@app.get("/orders")
async def orders_all():
    orders = get_orders()
    return {"orders": orders}

@app.post("/order/delete")
async def delete_order_api(request: Request):
    data = await request.json()
    order_id = data.get("order_id")
    if not order_id:
        return JSONResponse({"error": "ต้องระบุ order_id"}, status_code=400)
    delete_order(order_id)
    return {"success": True}

@app.post("/orders/cleanup")
async def cleanup_orders():
    deleted = delete_old_orders(hours=6)
    return {"deleted": deleted}
# ==============

init_chat()
initialize_database()
