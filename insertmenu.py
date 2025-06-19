from db import insert_menu

menu_list = [
    ("ต้มยำ", 99, "ต้มยำรสแซ่บ", "/Users/chidimon/Dev/Whisper/backend/image/Tomyum.jpg"),
    ("ข้าวผัด", 55, "ข้าวผัดไข่หอมๆ", "/Users/chidimon/Dev/Whisper/backend/image/ข้าวผัด.jpg"),
    ("ผัดกะเพรา", 60, "กะเพราไก่ไข่ดาว", "/Users/chidimon/Dev/Whisper/backend/image/ผัดกะเพรา.jpg"),
    ("ผัดไทย", 70, "ผัดไทยเส้นนุ่ม", "/Users/chidimon/Dev/Whisper/backend/image/ผัดไทย.jpg"),
    ("พิซซ่า", 129, "พิซซ่าชีสเยิ้ม", "/Users/chidimon/Dev/Whisper/backend/image/Pizza.jpg"),
    ("Pizza", 129, "Pizza cheese", "/Users/chidimon/Dev/Whisper/backend/image/Pizza.jpg"),
    ("Burger", 89, "เบอร์เกอร์เนื้อฉ่ำ", "/Users/chidimon/Dev/Whisper/backend/image/Burger.jpg"),
    ("Stake", 149, "สเต๊กหมูซอสพริกไทยดำ", "/Users/chidimon/Dev/Whisper/backend/image/Steak.jpg"),
    ("Fried Chicken", 99, "ไก่ทอดซอสเผ็ด", "/Users/chidimon/Dev/Whisper/backend/image/Fried_Chicken.jpg"),
    ("spaghetti", 79, "สปาเกตตี้ซอสมะเขือเทศ", "/Users/chidimon/Dev/Whisper/backend/image/Spaghetti.png"),
]

for name, price, desc, img in menu_list:
    insert_menu(name=name, price=price, description=desc, image_path=img)

print("เพิ่มเมนูสำเร็จ 10 รายการ")