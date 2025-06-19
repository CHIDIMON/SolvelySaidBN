# db.py (MongoDB version)

import os
import certifi
from pymongo import MongoClient # type: ignore
from bson.objectid import ObjectId



username = "chidimon"
password = "chidimon026"

MONGO_URI = f"mongodb+srv://{username}:{password}@solvelysaid.c6sojky.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
                     
print(MONGO_URI)
DB_NAME = "mydb"
COLLECTION = "menu"
IMAGE_DIR = 'image'

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
menu_col = db[COLLECTION]

def initialize_database():
    """สร้างเมนูเริ่มต้น (insert ถ้ายังไม่มีเมนูเลย)"""
    if menu_col.count_documents({}) == 0:
        # เพิ่ม Pizza
        pizza_path = os.path.join(IMAGE_DIR, "Pizza.webp")
        if os.path.exists(pizza_path):
            with open(pizza_path, "rb") as f:
                pizza_img = f.read()
            menu_col.insert_one({
                "name": "Pizza",
                "price": 129,
                "description": "พิซซ่าชีสเยิ้ม",
                "image": pizza_img
            })
        # เพิ่มต้มยำ (ชื่อไทย/อังกฤษ)
        tomyum_path = os.path.join(IMAGE_DIR, "Tomyum.jpg")
        if os.path.exists(tomyum_path):
            with open(tomyum_path, "rb") as f:
                tomyum_img = f.read()
            for name in ["ต้มยำ", "Tom Yum", "Tom Yam"]:
                menu_col.insert_one({
                    "name": name,
                    "price": 99,
                    "description": "ต้มยำกุ้งรสจัดจ้าน",
                    "image": tomyum_img
                })

def get_all_menus():
    """ดึงเมนูทั้งหมด (ไม่ดึงรูป)"""
    menus = []
    for doc in menu_col.find({}, {"image": 0}):
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        menus.append(doc)
    return menus

def get_menu_by_id(menu_id):
    """ดึงเมนูตาม id (ไม่ดึงรูป)"""
    doc = menu_col.find_one({"_id": ObjectId(menu_id)}, {"image": 0})
    if doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        return doc
    return None

def get_menu_by_name(menu_name):
    """ดึงเมนูตามชื่อ (ไม่ดึงรูป)"""
    doc = menu_col.find_one({"name": menu_name}, {"image": 0})
    if doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        return doc
    return None

def get_menu_image(menu_name):
    """ดึงรูปภาพเมนูตามชื่อ"""
    doc = menu_col.find_one({"name": menu_name}, {"image": 1})
    if doc and "image" in doc:
        return doc["image"]
    return None

def insert_menu(name, price=0, description="", image_path=None):
    """เพิ่มเมนูใหม่"""
    image_data = None
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_data = f.read()
    menu_col.insert_one({
        "name": name,
        "price": price,
        "description": description,
        "image": image_data
    })

def update_menu(menu_id, name=None, price=None, description=None, image_path=None):
    """แก้ไขข้อมูลเมนู (อัปเดตเฉพาะฟิลด์ที่ใส่)"""
    updates = {}
    if name is not None:
        updates["name"] = name
    if price is not None:
        updates["price"] = price
    if description is not None:
        updates["description"] = description
    if image_path is not None and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            updates["image"] = f.read()
    if not updates:
        return
    menu_col.update_one({"_id": ObjectId(menu_id)}, {"$set": updates})

def delete_menu(menu_id):
    """ลบเมนูตาม id"""
    menu_col.delete_one({"_id": ObjectId(menu_id)})
