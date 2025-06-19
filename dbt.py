from pymongo import MongoClient # type: ignore
from pprint import pprint

client = MongoClient("mongodb+srv://chidimon:chidimon026@solvelysaid.c6sojky.mongodb.net/?retryWrites=true&w=majority")
db = client['mydb']
menu_col = db['menu']

for menu in menu_col.find({}, {"_id": 0, "name": 1, "image": 1}):
    if 'image' in menu:
        size_mb = len(menu['image']) / (1024 * 1024)
        print(f"{menu['name']} : {size_mb:.2f} MB")
    else:
        print(f"{menu['name']} : no image")