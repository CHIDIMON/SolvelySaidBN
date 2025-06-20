import sys
import io
import os
import logging
import traceback
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from io import BytesIO
import sqlite3
from dotenv import load_dotenv
from chatapi import init_chat, chat_with_text
from whisperapi import transcribe_audio_api

# ตั้งค่า encoding เป็น UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app,
     resources={
         r"/upload": {"origins": "*"},
         r"/image/*": {"origins": "*"},
         r"/chat": {"origins": "*"},
         r"/ping": {"origins": "*"},
         r"/login": {
             "origins": [
                 "https://solvelysaid.space",
                 "http://127.0.0.1:5500"
             ]
         }
     },
     supports_credentials=True
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# โหลด env
load_dotenv()
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "default123")


# ================= ROUTES ===================

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        password = data.get("password", "")
        if password == LOGIN_PASSWORD:
            return jsonify({"success": True})
        return jsonify({"success": False}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200


@app.route('/image/<menu_name>', methods=['GET'])
def get_image(menu_name):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT image FROM menu WHERE name=?", (menu_name,))
        image_data = cursor.fetchone()
        conn.close()

        if image_data:
            return send_file(BytesIO(image_data['image']), mimetype='image/jpeg')
        return jsonify({"error": "ไม่พบรูปภาพ"}), 404
    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาด: {str(e)}")
        return jsonify({"error": "เกิดข้อผิดพลาดในการดึงรูปภาพ"}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "ไม่มีไฟล์ที่อัปโหลด"}), 400

    file = request.files['file']
    language = request.form.get('language', 'th')

    if not file.filename:
        return jsonify({"error": "ไม่ได้เลือกไฟล์"}), 400

    temp_path = None
    try:
        filename = file.filename or "temp.wav"
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)

        # ถอดเสียง
        text = transcribe_audio_api(temp_path, language=language)
        logging.info(f"Transcribed text: {text}")

        chat_response = chat_with_text(text, lang_code=language)

        # ตรวจสอบเมนู
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM menu")
        all_menus = [row['name'] for row in cursor.fetchall()]
        conn.close()

        matched_menu = next((name for name in all_menus if name.lower() in text.lower()), None)

        response_data = {
            "text": text,
            "chat_response": chat_response
        }
        if matched_menu:
            response_data["menu"] = matched_menu

        return jsonify(response_data)

    except Exception:
        logging.error("🔥 ERROR:\n" + traceback.format_exc())
        return jsonify({"error": "เกิดข้อผิดพลาดในการประมวลผล"}), 500

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    try:
        data = request.get_json()
        user_input = data.get('text', '')
        lang_code = data.get('language', 'th')

        if not user_input:
            return jsonify({'error': 'ไม่มีข้อความ'}), 400

        response = chat_with_text(user_input, lang_code=lang_code)
        return jsonify({'response': response})

    except Exception as e:
        logging.error(f"เกิดข้อผิดพลาดใน chat: {str(e)}")
        return jsonify({'error': 'เกิดข้อผิดพลาดในการสนทนา'}), 500


@app.route('/debug/menus', methods=['GET'])
def debug_menus():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM menu")
        menus = cursor.fetchall()
        conn.close()
        return jsonify({"menus": [{"id": m['id'], "name": m['name']} for m in menus]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def home():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>Welcome to solvelysaid.space</title>
      <link rel="icon" type="image/png" href="solvely.png" />
      <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600&display=swap" rel="stylesheet">
      <style>
        body {
          margin: 0;
          background: #000;
          color: white;
          font-family: 'Orbitron', sans-serif;
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
          text-align: center;
          padding: 0 20px;
          box-sizing: border-box;
        }

        .container {
          width: 100%;
          max-width: 960px;
        }

        h1 {
          font-size: 3rem;
          letter-spacing: 2px;
          margin-bottom: 20px;
          line-height: 1.3;
        }

        p {
          font-size: 1.2rem;
          color: #aaaaaa;
          margin-bottom: 16px;
        }

        a {
          display: inline-block;
          text-decoration: none;
          color: black;
          background: white;
          padding: 14px 30px;
          font-weight: bold;
          border-radius: 8px;
          font-size: 1rem;
          transition: background 0.3s ease, transform 0.2s ease;
        }

        a:hover {
          background: #00e5ff;
          transform: scale(1.05);
        }

        .highlight {
          color: #00e5ff;
        }

        @media (max-width: 768px) {
          h1 {
            font-size: 2rem;
            line-height: 1.3;
          }

          p {
            font-size: 1rem;
          }

          a {
            padding: 10px 22px;
            font-size: 0.95rem;
          }

          .container {
            max-width: 90%;
          }
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Welcome to<br><span class="highlight">solvelysaid.space</span></h1>
        <p>Mission: Backend API is running</p>
        <p><b>Thirasak.official</b></p>
        <a href="https://solvelysaid.space/">ENTER TO MAIN</a>
      </div>
    </body>
    </html>
    ''', 200

# ================= UTIL ===================

def get_db_connection():
    conn = sqlite3.connect('food_menu.db')
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = sqlite3.connect('food_menu.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image BLOB
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM menu")
    if cursor.fetchone()[0] == 0:
        with open("image/Pizza.webp", "rb") as f:
            pizza_img = f.read()
        cursor.execute("INSERT INTO menu (name, image) VALUES (?, ?)", ("Pizza", pizza_img))
        with open("image/Tomyum.jpg", "rb") as f:
            tomyum_img = f.read()
        cursor.execute("INSERT INTO menu (name, image) VALUES (?, ?)", ("ต้มยำ", tomyum_img))
        cursor.execute("INSERT INTO menu (name, image) VALUES (?, ?)", ("Tom Yum", tomyum_img))
        cursor.execute("INSERT INTO menu (name, image) VALUES (?, ?)", ("Tom Yam", tomyum_img))
    conn.commit()
    conn.close()


# ================= STARTUP ===================

if __name__ == '__main__':
    initialize_database()
    logging.info("Current menus in database:")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM menu")
    logging.info(cursor.fetchall())
    conn.close()

    init_chat()
    app.run(debug=False, port=5000, host='0.0.0.0')
