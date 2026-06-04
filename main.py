import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import datetime
import requests
import json
import os
import random
import base64

# ==========================================
# CẤU HÌNH HỆ THỐNG - ĐẲNG CẤP & UY TÍN
# ==========================================
ADMIN_ID = "8730269698"
BOT_KHACH_MOI = "8766548413:AAHtRBkwQLd2nT5Nig8v_F3MqRGb2hljLhk"
BOT_XU_LY_BILL = "8947479869:AAFCJZf4iaXg4FuPikDLeibRNaHJEx4CJWA"

bot = telebot.TeleBot(BOT_XU_LY_BILL)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.url_map.strict_slashes = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "lich_su_nap.json")
USER_FILE = os.path.join(BASE_DIR, "danh_sach_user.json") 

def load_history():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_users():
    if not os.path.exists(USER_FILE): return []
    with open(USER_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def save_users(data):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route("/")
def keep_alive():
    return "SERVER HUY ROYAL ĐANG CHẠY TRÊN RENDER!", 200

# ===== API ĐĂNG KÝ (CHỐNG TRÙNG LẶP TOÀN HỆ THỐNG) =====
@app.route("/api/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        phone = data.get("phone", "").strip()

        if not username or not password or not phone:
            return jsonify({"status": "error", "message": "Vui lòng nhập đủ thông tin!"}), 400

        users = load_users()
        for u in users:
            if u["username"].lower() == username.lower():
                return jsonify({"status": "error", "message": "❌ Tên tài khoản này đã có người sử dụng!"}), 400
            if u.get("phone") == phone:
                return jsonify({"status": "error", "message": "❌ Số điện thoại này đã được đăng ký!"}), 400

        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users.append({"username": username, "password": password, "phone": phone, "time": time_now})
        save_users(users)

        msg = f"🟢 CÓ KHÁCH HÀNG MỚI ĐĂNG KÝ\n👤 Tên: {username}\n📱 SĐT: {phone}\n⏰ T.Gian: {time_now}"
        requests.post(f"https://api.telegram.org/bot{BOT_KHACH_MOI}/sendMessage", json={"chat_id": ADMIN_ID, "text": msg})
        
        return jsonify({"status": "success", "message": "✅ Đăng ký thành công!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Lỗi máy chủ!"}), 500

# ===== API ĐĂNG NHẬP (ĐỒNG BỘ ĐIỆN THOẠI VÀ PC) =====
@app.route("/api/login", methods=["POST", "OPTIONS"])
def login_api():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.json
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        
        users = load_users()
        for u in users:
            if u["username"].lower() == username.lower():
                if u.get("password") == password:
                    return jsonify({"status": "success", "message": "Đăng nhập thành công!"}), 200
                else:
                    return jsonify({"status": "error", "message": "❌ Mật khẩu không chính xác!"}), 400
        
        return jsonify({"status": "error", "message": "❌ Tài khoản chưa được đăng ký!"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Lỗi máy chủ!"}), 500

@app.route("/api/deposit", methods=["POST", "OPTIONS"])
def deposit():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    try:
        data = request.json
        if not data: return jsonify({"status": "error", "message": "Không nhận được dữ liệu!"}), 400
        photo_base64 = data.get("photo_base64")
        username = data.get("username")
        tool_type = data.get("tool_type")
        tk_game = data.get("tk_game")
        tk_tool = data.get("tk_tool")
        if not all([photo_base64, username, tool_type, tk_game, tk_tool]):
            return jsonify({"status": "error", "message": "Thiếu thông tin hoặc ảnh!"}), 400
        try: image_data = base64.b64decode(photo_base64.split(",")[1])
        except Exception as e: return jsonify({"status": "error", "message": "File ảnh bị lỗi!"}), 400

        order_id = f"A{random.randint(10000, 99999)}"
        time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_record = {
            "id": order_id, "username": username, "time": time_now,
            "tool": tool_type, "tk_game": tk_game, "tk_tool": tk_tool,
            "bill": "⏳ Đang chờ Admin xét duyệt...", "code": "", "status": "pending"
        }
        history = load_history()
        history.insert(0, new_record)
        save_history(history)

        caption = (
            f"🚀 YÊU CẦU CẤP TOOL | #{order_id}\n\n"
            f"👤 Khách: {username}\n📦 Gói: {tool_type}\n"
            f"🎮 Game: {tk_game}\n🛠 Tool: {tk_tool}\n⏰ T.Gian: {time_now}\n\n"
            f"💡 HD CẤP MÃ: Chọn [Trả lời / Reply] tin nhắn này, gõ mã CODE và gửi đi!"
        )
        markup = InlineKeyboardMarkup()
        btn_duyet = InlineKeyboardButton("✅ DUYỆT NHANH (KO CODE)", callback_data=f"duyet_{order_id}")
        btn_huy = InlineKeyboardButton("❌ SAI BILL", callback_data=f"huy_{order_id}")
        markup.add(btn_duyet, btn_huy)

        bot.send_photo(ADMIN_ID, image_data, caption=caption, reply_markup=markup)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "Lỗi máy chủ!"}), 500

@app.route("/api/history", methods=["GET", "OPTIONS"])
def get_history():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200
    history = load_history()
    return jsonify({"data": history[:15]}), 200

@bot.callback_query_handler(func=lambda call: call.data.startswith("duyet_") or call.data.startswith("huy_"))
def handle_duyet_don(call):
    action, order_id = call.data.split("_")
    history = load_history()
    for record in history:
        if record["id"] == order_id:
            if action == "duyet":
                record["bill"] = "✅ Đã duyệt - Kích hoạt thành công"
                record["status"] = "success"
                bot.edit_message_caption(caption=call.message.caption + "\n\n✅ ĐÃ DUYỆT NHANH", chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.answer_callback_query(call.id, "Đã duyệt đơn!")
            elif action == "huy":
                record["bill"] = "❌ Bị hủy - Hóa đơn không hợp lệ"
                record["status"] = "error"
                bot.edit_message_caption(caption=call.message.caption + "\n\n❌ ĐÃ HỦY ĐƠN", chat_id=call.message.chat.id, message_id=call.message.message_id)
                bot.answer_callback_query(call.id, "Đã hủy đơn!")
            break
    save_history(history)

@bot.message_handler(func=lambda message: message.reply_to_message is not None)
def handle_reply_code(message):
    original_msg = message.reply_to_message
    if original_msg.caption and "YÊU CẦU CẤP TOOL | #" in original_msg.caption:
        try:
            order_id = original_msg.caption.split("| #")[1].split("\n")[0].strip()
            admin_text = message.text.replace("✅", "").replace("ĐÃ CẤP MÃ:", "").strip()
            history = load_history()
            for record in history:
                if record["id"] == order_id:
                    record["bill"] = "✅ Đã duyệt"
                    record["code"] = admin_text
                    record["status"] = "success"
                    break
            save_history(history)
            new_caption = original_msg.caption + f"\n\n➖➖➖➖➖➖\n✅ ĐÃ CẤP MÃ: {admin_text}"
            bot.edit_message_caption(caption=new_caption, chat_id=original_msg.chat.id, message_id=original_msg.message_id)
            bot.reply_to(message, f"🎯 Đã bắn mã {admin_text} lên bảng Lịch Sử Web!")
        except Exception as e:
            bot.reply_to(message, "❌ Lỗi: " + str(e))

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("🚀 HỆ THỐNG ĐÃ LÊN SÓNG SẴN SÀNG CHẠY 24/7!")
    bot.infinity_polling()
