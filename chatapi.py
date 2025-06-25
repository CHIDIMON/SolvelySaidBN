# -*- coding: utf-8 -*-
import os
import re
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# ✅ ดึง GROQ_API_KEY จาก Environment Variable
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

conversation_history = []
current_order = []
current_lang = "th"

def init_chat(lang_code="th"):
    global conversation_history, current_order, current_lang
    current_lang = lang_code

    if lang_code == "th":
        system_prompt = """
        คุณคือผู้ช่วยสั่งอาหาร
        - ตอบกลับทุกอย่างเป็นภาษาไทย
        - เมื่อผู้ใช้สั่งอาหาร ให้บันทึกรายการไว้เป็นข้อๆ โดยใส่เลขนำหน้าทุกรายการ เช่น
        1. ข้าวผัด x2
        2. ต้มยำกุ้ง x1
        - ถ้าผู้ใช้สั่งอาหารจำนวนหลายอย่าง ให้แสดงรายการทั้งหมดเป็นข้อ ๆ พร้อมเลข 1. 2. 3. ... เสมอ แม้ว่าจะมีรายการเดียวก็ต้องใส่เลขนำหน้า
        - เมื่อผู้ใช้พิมพ์ว่า 'สรุปเมนู' ให้แสดงรายการทั้งหมดที่บันทึกไว้ในรูปแบบข้อ ๆ พร้อมเลขกำกับ
        - พยายามสะกดให้ถูก ถ้ารูปประโยคแปลก หรือสะกดผิด ให้เดาเจตนาและแก้ไขให้ถูก
        - คำว่า 'reset' = รีเซ็ตสนทนา
        - ถ้าประโยคที่ผู้ใช้พิมพ์ไม่ชัดเจน ให้ถามกลับเพื่อยืนยัน
        """
    else:
        system_prompt = """
        You are a food ordering assistant for a restaurant in Thailand.
        - Always reply in Thai, except for the food item names (keep them in the original language the user typed).
        - When a user orders food, keep each menu item as a single entry in the order list, and always show a numbered list (1., 2., 3., ...) with the quantity for each item, for example:
        1. cheeseburger x3
        2. french fries x2
        - Even if there is only one item, always number it as '1.'
        - When showing the summary, always use this numbered list format.
        - When users mention English number words (one, two, three, four, five, etc.) or similar-sounding words (to, too, for, fore, ate, etc.), always interpret them as numbers (1, 2, 3, 4, 8, etc.), unless the context clearly says otherwise.
        - If the context is unclear, always ask the user to confirm the intended quantity.
        - If the user types 'summary', show the full list of orders in the above format.
        - If the user types 'reset', clear all previous orders and start a new conversation.
        - If a sentence is unclear or contains mistakes, do your best to interpret and correct it.
        """


    conversation_history.clear()
    current_order.clear()
    conversation_history.append({'role': 'system', 'content': system_prompt})

def summarize_order(menu_items):
    if not menu_items:
        return "ยังไม่มีเมนูที่ถูกสั่ง" if current_lang == "th" else "No items ordered yet."
    return ("📝 สรุปเมนูที่สั่ง:\n" if current_lang == "th" else "📝 Order Summary:\n") + "\n".join(
        f"{i+1}. {item['name']} - {item.get('note', 'ไม่มีหมายเหตุ' if current_lang == 'th' else 'No note')}"
        for i, item in enumerate(menu_items)
    )

def parse_menu_items(text):
    items = []
    lines = text.strip().split('\n')
    for line in lines:
        match = re.match(r'-\s*(.+?)\s*(\d+)\s*จาน(?:\s*\((.+?)\))?', line)
        if match:
            name = match.group(1).strip()
            quantity = int(match.group(2))
            note = match.group(3) if match.group(3) else ''
            for _ in range(quantity):
                items.append({'name': name, 'note': note})
    return items

def chat_with_text(user_input, lang_code="th"):
    global conversation_history, current_order, current_lang

    if not conversation_history or current_lang != lang_code:
        init_chat(lang_code)

    if user_input.lower().strip() == "reset":
        init_chat(lang_code)
        return "รีเซ็ตการสนทนาเรียบร้อยแล้ว" if lang_code == "th" else "Conversation reset."

    if user_input.lower().strip() in ["สรุปเมนู", "summary"]:
        return summarize_order(current_order)

    if any(word in user_input.lower() for word in ["สั่ง", "order"]):
        parts = user_input.split()
        if len(parts) >= 2:
            item_name = parts[1]
            note = " ".join(parts[2:]) if len(parts) > 2 else ""
            current_order.append({'name': item_name, 'note': note})
            return summarize_order(current_order)

    if "รายการสั่งอาหาร" in user_input:
        items = parse_menu_items(user_input)
        if items:
            current_order.extend(items)
            return summarize_order(current_order)

    conversation_history.append({'role': 'user', 'content': user_input})

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=conversation_history,
            temperature=0.7
        )
        if not response.choices:
            return "โมเดลไม่ตอบกลับ" if lang_code == "th" else "Model did not respond."

        content = getattr(response.choices[0].message, "content", "")
        reply = (content or "").strip()
        conversation_history.append({'role': 'assistant', 'content': reply})
        return reply
    except Exception as e:
        conversation_history.pop()
        return f"เกิดข้อผิดพลาด: {str(e)}" if lang_code == "th" else f"Error occurred: {str(e)}"
