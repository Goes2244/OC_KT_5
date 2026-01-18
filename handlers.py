import os
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from sqlalchemy.exc import SQLAlchemyError

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация базы данных будет отложена
db = None
Message = None
User = None


def init_models():
    """Ленивая инициализация моделей"""
    global Message, User
    if Message is None or User is None:
        from models import Message as Msg, User as Usr
        Message = Msg
        User = Usr


def get_db():
    """Получение экземпляра базы данных (ленивая инициализация)"""
    global db
    if db is None:
        from database import Database
        db = Database()
    return db


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    logger.info(f"User {user.id} started the bot")

    database = get_db()
    init_models()
    session = database.get_session()

    try:
        # Проверяем, есть ли пользователь в базе
        existing_user = session.query(User).filter_by(user_id=user.id).first()

        if existing_user:
            # Обновляем информацию
            existing_user.username = user.username
            existing_user.first_name = user.first_name
            existing_user.last_name = user.last_name
            logger.info(f"User {user.id} updated in database")
        else:
            # Создаем нового пользователя
            new_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(new_user)
            logger.info(f"User {user.id} added to database")

        session.commit()

        # Приветственное сообщение
        welcome_text = (
            "🤖 *Добро пожаловать в бот для лабораторной работы №5!*\n\n"
            f"👤 *Ваши данные:*\n"
            f"• ID: `{user.id}`\n"
            f"• Имя: {user.first_name or 'Не указано'}\n"
            f"• Username: @{user.username or 'Не указан'}\n\n"
            "📋 *Доступные команды:*\n"
            "• /start - Начать работу\n"
            "• /help - Помощь\n"
            "• /stats - Статистика\n"
            "• /mymessages - Мои сообщения\n"
            "• /allusers - Все пользователи (админ)\n\n"
            "💾 *Особенности:*\n"
            "• Все сообщения сохраняются в PostgreSQL\n"
            "• Данные сохраняются при перезапуске\n"
            "• Используется Docker контейнер\n\n"
            "📝 Просто отправьте мне любое сообщение, и оно будет сохранено!"
        )

        await update.message.reply_text(welcome_text, parse_mode='Markdown')

        # Сохраняем факт использования команды /start
        start_message = Message(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            message_text="/start command"
        )
        session.add(start_message)
        session.commit()

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in /start: {e}")
        await update.message.reply_text("❌ Произошла ошибка при работе с базой данных")
    finally:
        session.close()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "🆘 *Помощь по боту*\n\n"
        "*Команды:*\n"
        "• `/start` - Начало работы, регистрация\n"
        "• `/help` - Эта справка\n"
        "• `/stats` - Статистика бота\n"
        "• `/mymessages` - Ваши последние сообщения\n"
        "• `/allusers` - Список всех пользователей (только для админа)\n\n"
        "*Как это работает:*\n"
        "1. Бот работает в Docker контейнере\n"
        "2. Данные хранятся в PostgreSQL на вашем компьютере\n"
        "3. Все сообщения сохраняются в базе данных\n"
        "4. При перезапуске контейнера данные не теряются\n\n"
        "*Для лабораторной работы:*\n"
        "✓ Бот в Docker\n"
        "✓ PostgreSQL для хранения\n"
        "✓ Сохранение данных при перезапуске\n"
        "✓ Токен в переменных окружения\n\n"
        "📨 Просто отправьте текст - и он сохранится в БД!"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /stats"""
    user = update.effective_user
    logger.info(f"User {user.id} requested stats")

    database = get_db()
    init_models()
    session = database.get_session()

    try:
        # Получаем статистику
        total_messages = session.query(Message).count()
        total_users = session.query(User).count()
        user_messages = session.query(Message).filter_by(user_id=user.id).count()
        last_message = session.query(Message).order_by(Message.created_at.desc()).first()

        # Формируем ответ
        stats_text = (
            "📊 *Статистика бота*\n\n"
            f"*Общая статистика:*\n"
            f"• Всего сообщений: `{total_messages}`\n"
            f"• Всего пользователей: `{total_users}`\n\n"
            f"*Ваша статистика:*\n"
            f"• Ваших сообщений: `{user_messages}`\n"
            f"• Ваш ID: `{user.id}`\n\n"
        )

        if last_message:
            last_time = last_message.created_at.strftime("%d.%m.%Y %H:%M:%S")
            stats_text += f"*Последняя активность:*\n• {last_time}\n"

        stats_text += "\n🔄 *Перезапустите контейнер, чтобы проверить сохранение данных!*"

        await update.message.reply_text(stats_text, parse_mode='Markdown')

    except SQLAlchemyError as e:
        logger.error(f"Database error in /stats: {e}")
        await update.message.reply_text("❌ Ошибка при получении статистики")
    finally:
        session.close()


async def mymessages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /mymessages"""
    user = update.effective_user
    logger.info(f"User {user.id} requested their messages")

    database = get_db()
    init_models()
    session = database.get_session()

    try:
        # Получаем последние 10 сообщений пользователя
        messages = session.query(Message) \
            .filter_by(user_id=user.id) \
            .order_by(Message.created_at.desc()) \
            .limit(10) \
            .all()

        if not messages:
            await update.message.reply_text(
                "📭 У вас пока нет сохраненных сообщений.\n"
                "Отправьте любое сообщение, и оно появится здесь!"
            )
            return

        response = "📝 *Ваши последние сообщения:*\n\n"
        for i, msg in enumerate(reversed(messages), 1):
            time = msg.created_at.strftime("%d.%m %H:%M")
            text_preview = msg.message_text[:40] + "..." if len(msg.message_text) > 40 else msg.message_text
            response += f"{i}. *[{time}]* {text_preview}\n"

        response += f"\nВсего сообщений: {len(messages)}"

        await update.message.reply_text(response, parse_mode='Markdown')

    except SQLAlchemyError as e:
        logger.error(f"Database error in /mymessages: {e}")
        await update.message.reply_text("❌ Ошибка при получении сообщений")
    finally:
        session.close()


async def allusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /allusers (только для админа)"""
    user = update.effective_user
    logger.info(f"User {user.id} requested all users")

    # Проверка прав администратора
    admin_id = os.getenv('ADMIN_ID')
    if not admin_id or str(user.id) != admin_id:
        await update.message.reply_text(
            "⛔ Эта команда доступна только администратору.\n"
            f"Ваш ID: `{user.id}`\n"
            f"Требуемый ID: `{admin_id or 'не настроен'}`"
        )
        return

    database = get_db()
    init_models()
    session = database.get_session()

    try:
        # Получаем всех пользователей
        users = session.query(User).order_by(User.created_at.desc()).all()

        if not users:
            await update.message.reply_text("👥 В базе данных пока нет пользователей")
            return

        response = "👥 *Список всех пользователей:*\n\n"
        for i, u in enumerate(users, 1):
            created = u.created_at.strftime("%d.%m.%Y")
            last_seen = u.last_seen.strftime("%d.%m.%Y %H:%M") if u.last_seen else "никогда"
            username = f"@{u.username}" if u.username else "без username"
            response += f"{i}. {u.first_name} {username}\n"
            response += f"   ID: `{u.user_id}` | Регистрация: {created}\n"
            response += f"   Последняя активность: {last_seen}\n\n"

        response += f"Всего пользователей: {len(users)}"

        await update.message.reply_text(response, parse_mode='Markdown')

    except SQLAlchemyError as e:
        logger.error(f"Database error in /allusers: {e}")
        await update.message.reply_text("❌ Ошибка при получении списка пользователей")
    finally:
        session.close()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    message_text = update.message.text

    logger.info(f"Message from {user.id}: {message_text[:50]}...")

    database = get_db()
    init_models()
    session = database.get_session()

    try:
        # Сохраняем сообщение
        new_message = Message(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            message_text=message_text
        )

        # Обновляем информацию о пользователе
        existing_user = session.query(User).filter_by(user_id=user.id).first()
        if existing_user:
            existing_user.username = user.username
            existing_user.first_name = user.first_name
            existing_user.last_name = user.last_name
            logger.debug(f"User {user.id} updated")
        else:
            new_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(new_user)
            logger.info(f"New user {user.id} added")

        session.add(new_message)
        session.commit()

        # Подтверждение пользователю
        message_id = new_message.id
        created_at = new_message.created_at.strftime("%H:%M:%S")

        confirmation = (
            f"✅ *Сообщение сохранено!*\n\n"
            f"📝 Сообщение #{message_id}\n"
            f"🕐 Время: {created_at}\n"
            f"👤 От: {user.first_name or 'Пользователь'}\n\n"
            f"📊 *Проверьте сохранение:*\n"
            f"1. Используйте `/mymessages`\n"
            f"2. Остановите контейнер\n"
            f"3. Запустите снова\n"
            f"4. Сообщение должно сохраниться!\n\n"
            f"💾 БД: PostgreSQL | Контейнер: Docker"
        )

        await update.message.reply_text(confirmation, parse_mode='Markdown')

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error saving message: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении сообщения в базу данных")
    finally:
        session.close()


def setup_handlers(application):
    """Настройка обработчиков команд"""
    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("mymessages", mymessages_command))
    application.add_handler(CommandHandler("allusers", allusers_command))

    # Обработчик текстовых сообщений (исключая команды)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    logger.info("Handlers setup completed")