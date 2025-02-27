from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for frontend access

# Initialize the database
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# User registration
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"message": "All fields are required!"}), 400

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        conn.commit()
        conn.close()
        return jsonify({"message": "Registration successful!"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "Email already exists!"}), 400

# User login
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"message": "Invalid credentials!"}), 401

# Translation using Local LibreTranslate
@app.route("/translate", methods=["POST"])
def translate():
    try:
        # Detect if request is JSON or Form data
        if request.content_type == "application/json":
            data = request.get_json()
        else:
            data = request.form  # Handle form-encoded data

        print("🔍 Raw request data:", data)

        if not data:
            return jsonify({"message": "Invalid request: No data received"}), 400

        # Support both JSON & Form key names
        text = data.get("text") or data.get("q")  
        target_lang = data.get("targetLang") or data.get("target")

        if not text or not target_lang:
            return jsonify({"message": "Invalid request: Missing text or targetLang"}), 400

        target_lang = target_lang.lower()

        print(f"🔍 Received text for translation: {text}")
        print(f"🔍 Target language: {target_lang}")

        # LibreTranslate API request
        url = "https://api.mymemory.translated.net/get"
params = {
    "q": text,
    "langpair": f"auto|{target_lang}"
}
response = requests.get(url, params=params)
        payload = {"q": text, "source": "auto", "target": target_lang, "format": "text"}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(url, data=payload, headers=headers, timeout=10)
        result = response.json()

        print("🔹 LibreTranslate API Response:", result)

        if "translatedText" in result:
            return jsonify({"translatedText": result["translatedText"]}), 200
        else:
            return jsonify({"message": "Translation failed", "error": result}), 500

    except Exception as e:
        print("❌ Server Error:", str(e))
        return jsonify({"message": f"Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5002)
