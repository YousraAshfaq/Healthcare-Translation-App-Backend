from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
import requests

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "https://healthcare-translation-app.netlify.app"}},
     supports_credentials=True)


# Database Configuration (Uses PostgreSQL on Railway)
DATABASE_URL = os.getenv("DATABASE_URL")

def connect_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# Initialize the database (Users Table)
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# User Registration
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name, email, password = data.get("name"), data.get("email"), data.get("password")

    if not name or not email or not password:
        return jsonify({"message": "All fields are required!"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        conn.close()
        return jsonify({"message": "Registration successful!"}), 201
    except psycopg2.IntegrityError:
        return jsonify({"message": "Email already exists!"}), 400

# User Login
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email, password = data.get("email"), data.get("password")

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful!"}), 200
    return jsonify({"message": "Invalid credentials!"}), 401

# Translation using MyMemory API
#@app.route("/translate", methods=["POST"])
@app.route("/translate", methods=["POST", "OPTIONS"])
@cross_origin(origin="https://healthcare-translation-app.netlify.app", headers=["Content-Type"])
def translate():
    try:
        data = request.get_json()
        text, target_lang = data.get("text"), data.get("targetLang")

        if not text or not target_lang:
            return jsonify({"message": "Invalid request: Missing text or targetLang"}), 400

        print(f"🔍 Received text for translation: {text}")
        print(f"🔍 Target language: {target_lang}")

        # MyMemory API request
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair=en|{target_lang}"
        response = requests.get(url, timeout=10)
        result = response.json()

        translated_text = result.get("responseData", {}).get("translatedText", "")

        if translated_text:
            return jsonify({"translatedText": translated_text}), 200
        else:
            return jsonify({"message": "Translation failed", "error": result}), 500

    except Exception as e:
        print("❌ Server Error:", str(e))
        return jsonify({"message": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5002)
