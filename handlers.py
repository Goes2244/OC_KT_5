import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from sqlalchemy.exc import SQLAlchemyError
from database import Database
from models import Message, User

# Настройка логирования
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start
    Регистрирует пользователя и выводит приветственное сообщение
    """
    user = update.effective_user
    chat = update.effective_chat

    logger.info(f"Пользователь {user.id} (@{user.username}) начал работу с ботом")

    session = db.get_session()
    try:
        # Проверяем, есть ли пользователь в базе
        existing_user = session.query(User).filter_by(user_id=user.id).first()

        if existing_user:
            # Обновляем информацию о существующем пользователе
            existing_user.username = user.username
            existing_user.first_name = user.first_name
            existing_user.last_name = user.last_name
            existing_user.update_last_seen()
            logger.info(f"Пользователь {user.id} обновлен в базе данных")
        else:
            # Создаем нового пользователя
            new_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(new_user)
            logger.info(f"Новый пользователь {user.id} добавлен в базу данных")

        session.commit()

        # Формируем приветственное сообщение
        welcome_text = (
            "🤖 *Добро пожаловать в OC_KT_5_TBOT*\n\n"
            f"👤 *Ваши данные:*\n"
            f"• ID: `{user.id}`\n"
            f"• Имя: {user.first_name or 'Не указано'}\n"
            f"• Фамилия: {user.last_name or 'Не указана'}\n"
            f"• Username: @{user.username or 'не указан'}\n\n"
            "📋 *Доступные команды:*\n"
            "• `/start` - Начать работу\n"
            "• `/help` - Помощь и информация\n"
            "• `/stats` - Статистика бота\n"
            "• `/mymessages` - Ваши последние сообщения\n"
            "• `/allusers` - Все пользователи (только для администратора)\n\n"
            "📝 *Просто отправьте мне любое сообщение, и оно будет сохранено в базе данных!*"
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
        logger.error(f"Ошибка базы данных в /start: {e}")
        await update.message.reply_text("❌ Произошла ошибка при работе с базой данных. Пожалуйста, попробуйте позже.")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в /start: {e}")
        await update.message.reply_text("❌ Произошла непредвиденная ошибка.")
    finally:
        session.close()


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /help
    Выводит справку по командам и информацию о проекте
    """
    user = update.effective_user
    logger.info(f"Пользователь {user.id} запросил помощь")

    help_text = (
        "🆘 *Помощь по боту*\n\n"
        "*📋 Доступные команды:*\n"
        "• `/start` - Начало работы, регистрация в системе\n"
        "• `/help` - Эта справка\n"
        "• `/stats` - Статистика бота (сообщения, пользователи)\n"
        "• `/mymessages` - Показать ваши последние сообщения\n"
        "• `/allusers` - Список всех пользователей (доступно только администратору)\n\n"
        "*💡 Как это работает:*\n"
        "1. Все ваши сообщения сохраняются в базе данных PostgreSQL\n"
        "2. Бот работает внутри Docker контейнера\n"
        "3. Данные сохраняются при перезапуске контейнера\n"
        "4. Для хранения данных используются Docker volumes\n\n"
    )

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /stats
    Выводит статистику по сообщениям и пользователям
    """
    user = update.effective_user
    logger.info(f"Пользователь {user.id} запросил статистику")

    session = db.get_session()
    try:
        # Получаем статистику из базы данных
        total_messages = session.query(Message).count()
        total_users = session.query(User).count()

        # Сообщения текущего пользователя
        user_messages = session.query(Message).filter_by(user_id=user.id).count()

        # Последнее сообщение в системе
        last_message = session.query(Message).order_by(Message.created_at.desc()).first()

        # Формируем ответ
        stats_text = (
            "📊 *Статистика бота*\n\n"
            f"*Общая статистика:*\n"
            f"• Всего сообщений: `{total_messages}`\n"
            f"• Всего пользователей: `{total_users}`\n\n"
            f"*Ваша статистика:*\n"
            f"• Ваших сообщений: `{user_messages}`\n"
            f"• Ваш ID: `{user.id}`\n"
            f"• Ваш username: @{user.username or 'не указан'}\n\n"
        )

        if last_message:
            last_time = last_message.created_at.strftime("%d.%m.%Y %H:%M:%S")
            last_user = last_message.first_name or f"пользователь {last_message.user_id}"
            stats_text += f"*Последняя активность в системе:*\n• {last_time} ({last_user})\n"

        stats_text += "\n*Ваши данные в НЕнадежных руках :) *"

        await update.message.reply_text(stats_text, parse_mode='Markdown')

    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных в /stats: {e}")
        await update.message.reply_text("❌ Ошибка при получении статистики из базы данных")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в /stats: {e}")
        await update.message.reply_text("❌ Непредвиденная ошибка")
    finally:
        session.close()


async def mymessages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /mymessages
    Показывает последние сообщения пользователя
    """
    user = update.effective_user
    logger.info(f"Пользователь {user.id} запросил свои сообщения")

    session = db.get_session()
    try:
        # Получаем последние 10 сообщений пользователя
        messages = db.get_user_messages(user.id, limit=10)

        if not messages:
            await update.message.reply_text(
                "📭 *У вас пока нет сохраненных сообщений.*\n\n"
                "Просто отправьте мне любое сообщение, и оно появится здесь!\n"
                "Это отличная возможность проверить сохранение данных в лабораторной работе."
            )
            return

        # Формируем ответ
        response = "📝 *Ваши последние сообщения:*\n\n"

        for i, msg in enumerate(reversed(messages), 1):
            time = msg.created_at.strftime("%d.%m %H:%M")
            # Обрезаем длинный текст для лучшего отображения
            text_preview = msg.message_text[:40] + "..." if len(msg.message_text) > 40 else msg.message_text
            response += f"{i}. *[{time}]* {text_preview}\n"

        response += f"\nВсего сохранено сообщений: {len(messages)}"

        await update.message.reply_text(response, parse_mode='Markdown')

    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных в /mymessages: {e}")
        await update.message.reply_text("❌ Ошибка при получении ваших сообщений")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в /mymessages: {e}")
        await update.message.reply_text("❌ Непредвиденная ошибка")
    finally:
        session.close()


async def allusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /allusers
    Показывает всех пользователей бота (только для администратора)
    """
    user = update.effective_user
    logger.info(f"Пользователь {user.id} запросил список всех пользователей")

    # Проверка прав администратора
    admin_id = os.getenv('ADMIN_ID')
    if not admin_id or str(user.id) != admin_id:
        await update.message.reply_text(
            "⛔ *Эта команда доступна только администратору.*\n\n"
            f"Ваш ID: `{user.id}`\n"
        )
        return

    session = db.get_session()
    try:
        # Получаем всех пользователей
        users = session.query(User).order_by(User.created_at.desc()).all()

        if not users:
            await update.message.reply_text("👥 *В базе данных пока нет пользователей.*")
            return

        # Формируем ответ
        response = "👥 *Список всех пользователей бота:*\n\n"

        for i, u in enumerate(users, 1):
            created = u.created_at.strftime("%d.%m.%Y")
            last_seen = u.last_seen.strftime("%d.%m.%Y %H:%M") if u.last_seen else "никогда"
            username = f"@{u.username}" if u.username else "без username"

            response += f"{i}. *{u.first_name or 'Без имени'}* {username}\n"
            response += f"   ID: `{u.user_id}` | Регистрация: {created}\n"
            response += f"   Последняя активность: {last_seen}\n\n"

        response += f"Всего пользователей: {len(users)}"

        await update.message.reply_text(response, parse_mode='Markdown')

    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных в /allusers: {e}")
        await update.message.reply_text("❌ Ошибка при получении списка пользователей")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в /allusers: {e}")
        await update.message.reply_text("❌ Непредвиденная ошибка")
    finally:
        session.close()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик всех текстовых сообщений (кроме команд)
    Сохраняет сообщение в базу данных
    """
    user = update.effective_user
    message_text = update.message.text

    logger.info(f"Сообщение от {user.id}: {message_text[:50]}...")

    session = db.get_session()

    try:
        # Сохраняем сообщение в базу данных
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
            existing_user.update_last_seen()
            logger.debug(f"Информация о пользователе {user.id} обновлена")
        else:
            # Если пользователя нет в базе (маловероятно, но возможно)
            new_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(new_user)
            logger.info(f"Новый пользователь {user.id} добавлен при отправке сообщения")

        session.add(new_message)
        session.commit()

        # Формируем подтверждение пользователю
        message_id = new_message.id
        created_at = new_message.created_at.strftime("%H:%M:%S")

        confirmation = (
            f"✅ *Сообщение сохранено в базе данных!*\n\n"
            f"📝 *Детали сообщения:*\n"
            f"• ID сообщения: `{message_id}`\n"
            f"• Время сохранения: {created_at}\n"
            f"• Отправитель: {user.first_name or 'Пользователь'}\n\n"
        )

        await update.message.reply_text(confirmation, parse_mode='Markdown')

    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Ошибка базы данных при сохранении сообщения: {e}")
        await update.message.reply_text(
            "❌ Ошибка при сохранении сообщения в базу данных. Пожалуйста, попробуйте позже.")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при сохранении сообщения: {e}")
        await update.message.reply_text("❌ Непредвиденная ошибка при сохранении сообщения.")
    finally:
        session.close()


def setup_handlers(application):
    """
    Настройка всех обработчиков команд для бота
    """
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("mymessages", mymessages_command))
    application.add_handler(CommandHandler("allusers", allusers_command))

    # Регистрируем обработчик текстовых сообщений (исключая команды)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    logger.info("✅ Все обработчики команд успешно настроены")