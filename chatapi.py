# -*- coding: utf-8 -*-
import re
from openai import OpenAI

client = OpenAI(
    api_key="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",
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
        - เมื่อผู้ใช้สั่งอาหาร ให้บันทึกรายการไว้
        - เมื่อผู้ใช้พิมพ์ว่า 'สรุปเมนู' ให้แสดงรายการทั้งหมด
        - พยายามสะกดให้ถูกถ้ารูปประโยคแปลก
        - คำว่า 'reset' = รีเซ็ตสนทนา
        """
    else:
        system_prompt = """
        You are a food ordering assistant.
        - Always reply in English, even if the input is in another language.
        - When user orders food, store the item and any notes.
        - If user types 'summary', reply with all orders.
        - Try to spell correctly if the sentence structure is weird.
        - If user types 'reset', reset the conversation.
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

    # 👇 ตรวจสอบภาษาใหม่
    if not conversation_history or current_lang != lang_code:
        init_chat(lang_code)

    if user_input.lower().strip() == "reset":
        init_chat(lang_code)
        return "รีเซ็ตการสนทนาเรียบร้อยแล้ว" if lang_code == "th" else "Conversation reset."

    if user_input.lower().strip() in ["สรุปเมนู", "summary"]:
        return summarize_order(current_order)

    if "สั่ง" in user_input.lower():
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
        reply = response.choices[0].message.content.strip()
        conversation_history.append({'role': 'assistant', 'content': reply})
        return reply
    except Exception as e:
        conversation_history.pop()
        return f"เกิดข้อผิดพลาด: {str(e)}" if lang_code == "th" else f"Error occurred: {str(e)}"