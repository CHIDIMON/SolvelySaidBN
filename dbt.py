from pymongo import MongoClient
from tabulate import tabulate

client = MongoClient("mongodb+srv://chidimon:chidimon026@solvelysaid.c6sojky.mongodb.net/?retryWrites=true&w=majority")
db = client['mydb']
menu_col = db['menu']

table = []
for menu in menu_col.find({}, {"_id": 0, "name": 1, "price": 1, "description": 1, "image": 1}):
    if 'image' in menu and menu['image']:
        size_mb = len(menu['image']) / (1024 * 1024)
        img_size = f"{size_mb:.2f} MB"
    else:
        img_size = "no image"
    table.append([
        menu.get('name', ''),
        menu.get('price', ''),
        menu.get('description', ''),
        img_size
    ])

print(tabulate(table, headers=["Menu Name", "Price", "Description", "Image Size"], tablefmt="github"))