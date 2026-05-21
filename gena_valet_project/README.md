# 🤖 Telegram GPT Бот "Гена Валет"

Полнофункциональный Telegram-бот с AI-персонажем, системой подписок и готовностью к монетизации.

## 🚀 Возможности

- **AI-чат** — общение с харизматичным персонажем "Гена Валет" на базе GPT-4o-mini
- **Система подписок** — Free (10 сообщений/день), Premium Месяц (299₽), Premium Год (2490₽)
- **База данных** — PostgreSQL для хранения пользователей, сообщений и платежей
- **Контекстная память** — бот помнит историю диалога (последние 10 сообщений)
- **Админ-панель** — статистика по пользователям и платежам через команду `/admin`
- **Платежи** — готовность к интеграции CryptoBot (USDT) или других платёжных систем
- **Docker** — развёртывание одной командой

## 📁 Структура проекта

```
/workspace
├── gena_valet_bot.py      # Основной код бота
├── docker-compose.yml     # Конфигурация Docker (бот + PostgreSQL)
├── Dockerfile             # Образ для контейнера бота
├── requirements.txt       # Python-зависимости
├── .env.example          # Шаблон переменных окружения
└── README.md             # Эта инструкция
```

## 🔧 Быстрый запуск (Docker)

### 1. Клонировать/скопировать файлы
Убедитесь, что все файлы из структуры выше находятся в одной папке.

### 2. Настроить переменные окружения
```bash
cp .env.example .env
```

Откройте `.env` и заполните:
- `TELEGRAM_TOKEN` — токен бота от [@BotFather](https://t.me/BotFather)
- `OPENAI_API_KEY` — ключ API от [OpenAI Platform](https://platform.openai.com)
- `ADMIN_IDS` — ваш Telegram ID (узнать через [@userinfobot](https://t.me/userinfobot))
- `PROJECT_CHANNEL` — ссылка на ваш Telegram-канал
- `PROJECT_WEBSITE` — ссылка на сайт проекта

**Опционально:**
- `CRYPTOBOT_TOKEN` — токен для приёма платежей в криптовалюте ([CryptoBot](https://crypto.bot/))

### 3. Запустить бота
```bash
docker-compose up -d --build
```

### 4. Проверить работу
```bash
docker-compose logs -f bot
```

Бот готов! Напишите ему в Telegram.

## 🖥️ Локальный запуск (без Docker)

### 1. Установить PostgreSQL
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS (через Homebrew)
brew install postgresql
```

### 2. Создать базу данных
```bash
sudo -u postgres psql
CREATE DATABASE gena_valet_bot;
CREATE USER gena_user WITH PASSWORD 'gena_password_secure_123';
GRANT ALL PRIVILEGES ON DATABASE gena_valet_bot TO gena_user;
\q
```

### 3. Установить зависимости
```bash
pip install -r requirements.txt
```

### 4. Настроить .env
```bash
cp .env.example .env
# Отредактируйте DATABASE_URL на:
# DATABASE_URL=postgresql://gena_user:gena_password_secure_123@localhost:5432/gena_valet_bot
```

### 5. Запустить
```bash
python gena_valet_bot.py
```

## 💰 Настройка платежей

### CryptoBot (криптовалюта)
1. Зарегистрируйтесь в [@CryptoBot](https://t.me/CryptoBot)
2. Создайте приложение и получите токен
3. Добавьте токен в `.env`:
   ```
   CRYPTOBOT_TOKEN=ваш_токен_от_cryptobot
   ```
4. Перезапустите бота

### ЮKassa / другие платёжки
Для подключения других платёжных систем отредактируйте функцию `process_payment()` в `gena_valet_bot.py`.

## 📊 Администрирование

### Команды администратора
- `/admin` — показать статистику бота (доступно только для ID из `ADMIN_IDS`)

### Просмотр логов
```bash
# Docker
docker-compose logs -f bot

# Локально
# Логи выводятся в консоль при запуске
```

## 🎨 Настройка персонажа

Откройте `gena_valet_bot.py` и найдите класс `AILogic`. Измените `system_prompt` для настройки характера "Гены Валета":

```python
self.system_prompt = """
Ты — Гена Валет, харизматичный AI-персонаж...
"""
```

## 🔐 Безопасность

- ✅ Проверка прав администратора для `/admin`
- ✅ Защита от SQL-инъекций (используются параметризованные запросы)
- ✅ Лимиты сообщений для бесплатных пользователей
- ✅ Проверка срока действия подписки

## 📈 Масштабирование

Для высоких нагрузок:
1. Используйте managed PostgreSQL (AWS RDS, Google Cloud SQL, Yandex Cloud)
2. Настройте кэширование (Redis) для истории сообщений
3. Разверните бота на нескольких репликах через webhook вместо polling
4. Используйте очередь задач (Celery + Redis) для асинхронной обработки

## 🛠️ Технологии

- **Python 3.11+**
- **aiogram 3.x** — фреймворк для Telegram-ботов
- **OpenAI GPT-4o-mini** — AI-модель
- **PostgreSQL** — база данных
- **asyncpg** — асинхронный драйвер PostgreSQL
- **Docker & Docker Compose** — контейнеризация

## 📞 Поддержка

Вопросы и предложения: добавьте контакт в этот README.

## 📝 Лицензия

MIT

---

**Проект "Гена Валет"** © 2024  
AI-персонаж для создания вирусного контента и монетизации аудитории.
