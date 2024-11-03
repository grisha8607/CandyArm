import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta

# Токен для Telegram бота
TELEGRAM_BOT_TOKEN = "7657364903:AAHCZDhVrB2nyqeDGeYmJfoetTUILS4JMEc"

# Настройка Flask-приложения и базы данных
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///candy_game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Максимум пользователей
MAX_USERS = 5000000

# Модель пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    telegram_id = db.Column(db.String(100), nullable=True)
    last_claim = db.Column(db.DateTime, nullable=True)
    balance = db.Column(db.Integer, default=0)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

# Создание базы данных
with app.app_context():
    db.create_all()

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if User.query.count() >= MAX_USERS:
        await update.message.reply_text("Максимум пользователей достигнут.")
        return

    user = User.query.filter_by(telegram_id=str(user_id)).first()
    if user:
        await update.message.reply_text("Вы уже зарегистрированы!")
    else:
        new_user = User(username=username, telegram_id=str(user_id))
        db.session.add(new_user)
        db.session.commit()
        await update.message.reply_text("Регистрация в Candy Game прошла успешно!")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user = User.query.filter_by(telegram_id=str(user_id)).first()

    if user:
        await update.message.reply_text(f"Ваш баланс: {user.balance}")
    else:
        await update.message.reply_text("Вы не зарегистрированы. Используйте /start для регистрации.")

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user = User.query.filter_by(telegram_id=str(user_id)).first()

    if not user:
        await update.message.reply_text("Вы не зарегистрированы.")
        return

    now = datetime.utcnow()
    if user.last_claim and (now - user.last_claim) < timedelta(hours=24):
        await update.message.reply_text("Награда доступна раз в 24 часа.")
    else:
        user.balance += 500
        user.last_claim = now
        db.session.commit()
        await update.message.reply_text("Награда получена! Баланс обновлен.")

# Запуск бота
if __name__ == '__main__':
    app_telegram = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("balance", balance))
    app_telegram.add_handler(CommandHandler("claim", claim))

    print("Бот запущен.")
    app_telegram.run_polling()
