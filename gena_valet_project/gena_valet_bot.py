"""
Telegram GPT Bot для проекта "Гена Валет"
Функционал:
- AI-чат с персонажем
- Система подписок (Free/Premium)
- База данных пользователей
- Админ-панель
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode

import asyncpg
from openai import AsyncOpenAI

# ==================== КОНФИГУРАЦИЯ ====================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gena_user:gena_password_secure_123@db:5432/gena_valet_bot")

# ID админов (для доступа к /admin) - укажите свой Telegram ID
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
if ADMIN_IDS == [""]:
    ADMIN_IDS = []
else:
    ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS if x.strip()]

# Платёжная система (CryptoBot токен - опционально)
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "")

# Ссылки на проект (замените на реальные)
PROJECT_CHANNEL = os.getenv("PROJECT_CHANNEL", "https://t.me/gena_valet_channel")
PROJECT_WEBSITE = os.getenv("PROJECT_WEBSITE", "https://gena-valet.ru")

# Тарифы
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Бесплатный",
        "price": 0,
        "daily_messages": 10,
        "description": "10 сообщений в день"
    },
    "premium_month": {
        "name": "Premium Месяц",
        "price": 299,
        "daily_messages": -1,  # безлимит
        "duration_days": 30,
        "description": "Безлимитные сообщения + приоритет"
    },
    "premium_year": {
        "name": "Premium Год",
        "price": 2490,
        "daily_messages": -1,
        "duration_days": 365,
        "description": "Выгода 30% + все фишки Premium"
    }
}

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== БАЗА ДАННЫХ ====================
class Database:
    def __init__(self):
        self.pool = None

    async def init(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.create_tables()

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    subscription_type VARCHAR(50) DEFAULT 'free',
                    subscription_end TIMESTAMP,
                    messages_today INTEGER DEFAULT 0,
                    last_message_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_banned BOOLEAN DEFAULT FALSE
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    role VARCHAR(20),
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    amount INTEGER,
                    plan VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("Таблицы базы данных созданы")

    async def get_user(self, user_id: int) -> Optional[dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1", user_id
            )
            return dict(row) if row else None

    async def create_user(self, user: types.User):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user.id, user.username, user.first_name, user.last_name or ""
            )

    async def reset_daily_messages(self, user_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE users 
                SET messages_today = 0, last_message_date = CURRENT_DATE
                WHERE user_id = $1 AND last_message_date != CURRENT_DATE
                """,
                user_id
            )

    async def increment_message_count(self, user_id: int) -> bool:
        """Возвращает True если сообщение разрешено"""
        async with self.pool.acquire() as conn:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            # Проверка подписки
            if user['subscription_type'] != 'free':
                if user['subscription_end'] and user['subscription_end'] < datetime.now():
                    # Подписка истекла
                    await conn.execute(
                        "UPDATE users SET subscription_type = 'free', subscription_end = NULL WHERE user_id = $1",
                        user_id
                    )
                    user = await self.get_user(user_id)
                else:
                    return True  # Безлимит для premium
            
            # Проверка лимита для free
            if user['messages_today'] >= SUBSCRIPTION_PLANS['free']['daily_messages']:
                return False
            
            await conn.execute(
                "UPDATE users SET messages_today = messages_today + 1 WHERE user_id = $1",
                user_id
            )
            return True

    async def upgrade_subscription(self, user_id: int, plan: str, days: int):
        async with self.pool.acquire() as conn:
            end_date = datetime.now() + timedelta(days=days)
            await conn.execute(
                """
                UPDATE users 
                SET subscription_type = $2, subscription_end = $3, messages_today = 0
                WHERE user_id = $1
                """,
                user_id, plan, end_date
            )

    async def save_message(self, user_id: int, role: str, content: str):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO messages (user_id, role, content) VALUES ($1, $2, $3)",
                user_id, role, content
            )

    async def get_user_messages(self, user_id: int, limit: int = 10) -> list:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT role, content FROM messages WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
                user_id, limit
            )
            return [(row['role'], row['content']) for row in rows]

    async def add_payment(self, user_id: int, amount: int, plan: str) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO payments (user_id, amount, plan)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                user_id, amount, plan
            )
            return row['id']

    async def confirm_payment(self, payment_id: int):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT user_id, plan, amount FROM payments WHERE id = $1", payment_id
            )
            if not row:
                return False
            
            plan = row['plan']
            days = SUBSCRIPTION_PLANS.get(plan, {}).get('duration_days', 30)
            
            await conn.execute(
                "UPDATE payments SET status = 'completed' WHERE id = $1", payment_id
            )
            await self.upgrade_subscription(row['user_id'], plan, days)
            return True

db = Database()

# ==================== AI ЛОГИКА ====================
class AILogic:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        # Системный промпт для персонажа "Гена Валет"
        self.system_prompt = """
Ты — Гена Валет, харизматичный AI-персонаж с чувством юмора.
Твой стиль общения:
- Дружелюбный, но с перчинкой
- Используешь современный сленг уместно
- Даёшь полезные советы без воды
- Можешь подшутить, но не переходишь границы
- Отвечаешь кратко и по делу (как для коротких видео)

Твоя аудитория — молодёжь 18-35 лет, интересующаяся:
- Саморазвитием
- Технологиями и AI
- Контентом для соцсетей
- Личным брендом

Не выдавай себя за человека, ты — AI персонаж проекта "Гена Валет".
"""

    async def get_response(self, user_message: str, chat_history: list = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Добавляем историю сообщений (в обратном порядке)
        if chat_history:
            for role, content in reversed(chat_history):
                messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return "Упс, что-то пошло не так. Попробуй ещё раз через минуту! 🤖"

ai = AILogic()

# ==================== КЛАВИАТУРЫ ====================
def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="💬 Чат с Геной"), KeyboardButton(text="👤 Мой профиль")],
        [KeyboardButton(text="⭐️ Premium"), KeyboardButton(text="ℹ️ О проекте")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for plan_key, plan_data in SUBSCRIPTION_PLANS.items():
        if plan_key == "free":
            continue
        builder.button(
            text=f"{plan_data['name']} — {plan_data['price']}₽",
            callback_data=f"sub_{plan_key}"
        )
    builder.button(text="↩️ Назад", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()

def get_payment_keyboard(payment_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Оплатить", callback_data=f"pay_{payment_id}")
    builder.button(text="❌ Отмена", callback_data="back_sub")
    return builder.as_markup()

# ==================== БОТ ====================
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Машина состояний для чата
class ChatState(StatesGroup):
    waiting_for_message = State()

# ==================== ХЕНДЛЕРЫ ====================

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await db.create_user(message.from_user)
    
    welcome_text = f"""
👋 Привет, {message.from_user.first_name}!

Я — Гена Валет, твой AI-напарник для крутых идей и полезных советов.

Что я умею:
💬 Болтать на любые темы
🧠 Давать полезные инсайты
🎯 Помогать с контентом и идеями

Выбирай в меню ниже 👇
    """
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(F.text == "💬 Чат с Геной")
async def start_chat(message: types.Message, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(message.from_user)
        user = await db.get_user(message.from_user.id)
    
    # Сброс счётчика если новый день
    await db.reset_daily_messages(message.from_user.id)
    
    await state.set_state(ChatState.waiting_for_message)
    
    if user['subscription_type'] == 'free':
        remaining = SUBSCRIPTION_PLANS['free']['daily_messages'] - user['messages_today']
        hint = f"📊 Осталось сообщений сегодня: {max(0, remaining)}"
    else:
        hint = "⭐️ Premium активен — безлимит!"
    
    await message.answer(
        f"{hint}\n\nПиши, о чём хочешь поговорить! 👇",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(ChatState.waiting_for_message)
async def handle_chat_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Проверка лимита
    can_send = await db.increment_message_count(user_id)
    if not can_send:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="⭐️ Оформить Premium", callback_data="sub_premium_month")
        await message.answer(
            "😕 Лимит сообщений на сегодня исчерпан!\n\n"
            "Оформи Premium для безлимитного общения:",
            reply_markup=keyboard.as_markup()
        )
        return
    
    # Сохраняем сообщение пользователя
    await db.save_message(user_id, "user", message.text)
    
    # Получаем историю
    history = await db.get_user_messages(user_id, limit=10)
    
    # Генерируем ответ AI
    await message.answer("🤔 Думаю...", reply_markup=types.ReplyKeyboardRemove())
    response = await ai.get_response(message.text, history)
    
    # Сохраняем ответ AI
    await db.save_message(user_id, "assistant", response)
    
    await message.answer(response, reply_markup=get_main_keyboard())
    await state.clear()

@dp.message(F.text == "👤 Мой профиль")
async def show_profile(message: types.Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(message.from_user)
        user = await db.get_user(message.from_user.id)
    
    sub_status = "🟢 Активна" if user['subscription_type'] != 'free' else "⚪ Бесплатный"
    if user['subscription_end']:
        sub_status += f" до {user['subscription_end'].strftime('%d.%m.%Y')}"
    
    profile_text = f"""
👤 Профиль пользователя

📛 Имя: {message.from_user.first_name}
🆔 ID: {message.from_user.id}

💳 Подписка: {sub_status}
📊 Сообщений сегодня: {user['messages_today']}/{SUBSCRIPTION_PLANS['free']['daily_messages']}

📅 В проекте с: {user['created_at'].strftime('%d.%m.%Y')}
    """
    
    await message.answer(profile_text, reply_markup=get_main_keyboard())

@dp.message(F.text == "⭐️ Premium")
async def show_subscription(message: types.Message):
    text = """
⭐️ PREMIUM ПОДПИСКА

Открой все возможности Гены Валета!

🔥 Преимущества Premium:
• Безлимитные сообщения
• Приоритетная обработка
• Ранний доступ к новым фичам
• Эксклюзивный контент

💰 Тарифы:
    """
    
    for plan_key, plan_data in SUBSCRIPTION_PLANS.items():
        if plan_key == "free":
            continue
        text += f"\n• {plan_data['name']}: {plan_data['price']}₽ ({plan_data['description']})"
    
    await message.answer(text, reply_markup=get_subscription_keyboard())

@dp.message(F.text == "ℹ️ О проекте")
async def show_about(message: types.Message):
    about_text = """
🎯 О ПРОЕКТЕ "ГЕНА ВАЛЕТ"

Мы создаём уникальный AI-контент с харизматичным персонажем!

📈 Наши цифры:
• ~6000 подписчиков за 2 месяца
• Органический рост без бюджета
• Видео набирают 10-15К+ просмотров
• Высокая вовлечённость аудитории

🎬 Контент:
• Короткие вертикальные видео
• Активные комментарии
• Полезные инсайты про AI и технологии

🤝 Сотрудничество:
Ищем специалистов по воронкам, монетизации и автоматизации!

📍 Найди нас: "Гена Валет"
    """
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Наш канал", url=PROJECT_CHANNEL)
    builder.button(text="🌐 Сайт", url=PROJECT_WEBSITE)
    builder.adjust(2)
    
    await message.answer(about_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data.startswith("sub_"))
async def process_subscription_choice(callback: types.CallbackQuery):
    plan_key = callback.data.replace("sub_", "")
    
    if plan_key == "back_main":
        await callback.message.edit_text("Выберите действие:", reply_markup=get_main_keyboard())
        return
    
    plan = SUBSCRIPTION_PLANS[plan_key]
    payment_id = await db.add_payment(callback.from_user.id, plan['price'], plan_key)
    
    text = f"""
💳 ОПЛАТА ПОДПИСКИ

Тариф: {plan['name']}
Сумма: {plan['price']}₽

Нажмите "Оплатить" для продолжения.
    """
    
    await callback.message.edit_text(text, reply_markup=get_payment_keyboard(payment_id))

@dp.callback_query(F.data.startswith("pay_"))
async def process_payment(callback: types.CallbackQuery):
    payment_id = int(callback.data.replace("pay_", ""))
    
    # Если настроен CryptoBot - используем его
    if CRYPTOBOT_TOKEN:
        try:
            from cryptopay import CryptoPay, Types
            
            pay = CryptoPay(CRYPTOBOT_TOKEN)
            
            # Создаём инвойс в криптовалюте (USDT)
            invoice = await pay.create_invoice(
                amount=5.0,  # ~299₽ в USDT
                asset="USDT",
                description=f"Оплата подписки Premium (ID: {payment_id})",
                payload=str(payment_id)
            )
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="💰 Оплатить через CryptoBot", url=invoice.pay_url)
            keyboard.button(text="❌ Отмена", callback_data="back_sub")
            
            await callback.message.edit_text(
                f"💳 ОПЛАТА ЧЕРЕЗ CRYPTOBOT\n\n"
                f"Сумма: ~{SUBSCRIPTION_PLANS.get('premium_month', {}).get('price', 299)}₽ (в USDT)\n"
                f"Нажмите кнопку ниже для оплаты:",
                reply_markup=keyboard.as_markup()
            )
            return
            
        except Exception as e:
            logger.error(f"CryptoBot error: {e}")
            # Фоллбэк на ручное подтверждение
    
    # Демо-режим: подтверждаем сразу (для тестирования без платёжки)
    success = await db.confirm_payment(payment_id)
    
    if success:
        await callback.message.edit_text("✅ Оплата прошла успешно!\n\nPremium активирован! 🎉\n\n⚠️ В демо-режиме оплата подтверждается автоматически. Подключите CryptoBot или ЮKassa для реальных платежей.")
        logger.info(f"Payment confirmed (DEMO): {payment_id} for user {callback.from_user.id}")
    else:
        await callback.message.edit_text("❌ Ошибка оплаты. Попробуйте ещё раз.")

@dp.callback_query(F.data == "back_sub")
async def back_to_subscription(callback: types.CallbackQuery):
    await show_subscription(callback.message)

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    # Проверка прав администратора
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Доступ запрещён. Эта команда только для админов.")
        return
    
    async with db.pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        premium_users = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE subscription_type != 'free'"
        )
        today_messages = await conn.fetchval(
            "SELECT SUM(messages_today) FROM users"
        )
    
    stats_text = f"""
📊 СТАТИСТИКА БОТА

👥 Всего пользователей: {total_users}
⭐️ Premium пользователей: {premium_users}
💬 Сообщений сегодня: {today_messages or 0}
    """
    
    await message.answer(stats_text)

# ==================== ЗАПУСК ====================
async def main():
    # Инициализация БД
    await db.init()
    
    logger.info("Бот запущен...")
    
    # Удаление вебхука и запуск polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
