import os
import certifi
from pymongo import MongoClient
from bson.objectid import ObjectId
from PIL import Image
import io
from datetime import datetime, timedelta

MONGO_URI = "mongodb+srv://chidimon:chidimon026@solvelysaid.c6sojky.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsCAFile=certifi.where()
)

print(MONGO_URI)
DB_NAME = "mydb"
COLLECTION = "menu"
IMAGE_DIR = 'image'

db = client[DB_NAME]
menu_col = db[COLLECTION]

def initialize_database():
    if menu_col.count_documents({}) == 0:
        pizza_path = os.path.join(IMAGE_DIR, "Pizza.webp")
        if os.path.exists(pizza_path):
            image_thumb, image_720p = process_images(pizza_path)
            menu_col.insert_one({
                "name": "Pizza",
                "price": 129,
                "description": "พิซซ่าชีสเยิ้ม",
                "image_thumb": image_thumb,
                "image_720p": image_720p,
            })
        tomyum_path = os.path.join(IMAGE_DIR, "Tomyum.jpg")
        if os.path.exists(tomyum_path):
            image_thumb, image_720p = process_images(tomyum_path)
            for name in ["ต้มยำ", "Tom Yum", "Tom Yam"]:
                menu_col.insert_one({
                    "name": name,
                    "price": 99,
                    "description": "ต้มยำกุ้งรสจัดจ้าน",
                    "image_thumb": image_thumb,
                    "image_720p": image_720p,
                })

def process_images(image_path):
    image_thumb = None
    image_720p = None
    if image_path and os.path.exists(image_path):
        with Image.open(image_path) as img:
            img_thumb = img.copy().convert("RGB")
            img_thumb.thumbnail((128, 128))
            buf_thumb = io.BytesIO()
            img_thumb.save(buf_thumb, format="JPEG", quality=75)
            image_thumb = buf_thumb.getvalue()
            img_720 = img.copy().convert("RGB")
            img_720.thumbnail((1280, 720))
            buf_720 = io.BytesIO()
            img_720.save(buf_720, format="JPEG", quality=85)
            image_720p = buf_720.getvalue()
    return image_thumb, image_720p

def get_all_menus():
    menus = []
    for doc in menu_col.find({}, {"image_thumb": 0, "image_720p": 0}):
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        menus.append(doc)
    return menus

def get_menu_by_id(menu_id):
    doc = menu_col.find_one({"_id": ObjectId(menu_id)}, {"image_thumb": 0, "image_720p": 0})
    if doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        return doc
    return None

def get_menu_by_name(menu_name):
    doc = menu_col.find_one({"name": menu_name}, {"image_thumb": 0, "image_720p": 0})
    if doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        return doc
    return None

def get_menu_image_thumb(menu_name):
    doc = menu_col.find_one({"name": menu_name}, {"image_thumb": 1})
    if doc and "image_thumb" in doc:
        return doc["image_thumb"]
    return None

def get_menu_image_720p(menu_name):
    doc = menu_col.find_one({"name": menu_name}, {"image_720p": 1})
    if doc and "image_720p" in doc:
        return doc["image_720p"]
    return None

def insert_menu(name, price=0, description="", image_path=None):
    image_thumb, image_720p = process_images(image_path)
    menu_col.insert_one({
        "name": name,
        "price": price,
        "description": description,
        "image_thumb": image_thumb,
        "image_720p": image_720p,
    })

def update_menu(menu_id, name=None, price=None, description=None, image_path=None):
    updates = {}
    if name is not None:
        updates["name"] = name
    if price is not None:
        updates["price"] = price
    if description is not None:
        updates["description"] = description
    if image_path is not None and os.path.exists(image_path):
        image_thumb, image_720p = process_images(image_path)
        updates["image_thumb"] = image_thumb
        updates["image_720p"] = image_720p
    if not updates:
        return
    menu_col.update_one({"_id": ObjectId(menu_id)}, {"$set": updates})

def delete_menu(menu_id):
    menu_col.delete_one({"_id": ObjectId(menu_id)})

# ==== ORDER ====
ORDER_COLLECTION = "orders"
order_col = db[ORDER_COLLECTION]

def add_order(table_number, menus, summary=None):
    doc = {
        "table_number": table_number,
        "menus": menus,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "waiting"
    }
    if summary:
        doc["summary"] = summary
    order_col.insert_one(doc)

def get_orders(table_number=None):
    query = {}
    if table_number:
        query["table_number"] = table_number
    orders = []
    for doc in order_col.find(query):
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        orders.append(doc)
    return orders

def delete_order(order_id):
    order_col.delete_one({"_id": ObjectId(order_id)})

def update_order_status(order_id, status):
    order_col.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": status}})

def delete_old_orders(hours=6):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    res = order_col.delete_many({
        "timestamp": {"$lt": cutoff.isoformat()}
    })
    return res.deleted_count
