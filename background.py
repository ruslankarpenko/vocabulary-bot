from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот працює! 🚀"

@app.route('/health')
def health():
    return "OK", 200

def run():
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Запуск веб-сервера для підтримки бота активним"""
    t = Thread(target=run)
    t.start()
