from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот працює! 🚀"

@app.route('/health')
def health():
    return "OK", 200

def run():
    app.run(host='0.0.0.0', port=80)

def keep_alive():
    """Запуск веб-сервера для підтримки бота активним"""
    t = Thread(target=run)
    t.start()