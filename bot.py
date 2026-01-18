import os
import logging
from telegram.ext import Application
from dotenv import load_dotenv
from database import Database
from handlers import setup_handlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def check_environment():
    """Проверка необходимых переменных окружения"""
    required_vars = ['BOT_TOKEN', 'DATABASE_URL']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        error_msg = f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}"
        logger.error(error_msg)
        print("\n" + "=" * 60)
        print("ОШИБКА КОНФИГУРАЦИИ")
        print("=" * 60)
        print("Создайте файл .env со следующими переменными:")
        print("BOT_TOKEN=ваш_токен_бота")
        print("DATABASE_URL=postgresql://postgres@host.docker.internal:5433/telegram_bot_db")
        print("\nДля получения токена создайте бота через @BotFather в Telegram")
        print("=" * 60)
        raise ValueError(error_msg)


def main():
    """Основная функция запуска бота"""
    try:
        # Загрузка переменных окружения
        load_dotenv()

        # Проверка переменных окружения
        check_environment()

        # Получение токена бота
        BOT_TOKEN = os.getenv('BOT_TOKEN')

        logger.info("Starting Telegram Bot for Lab 5")
        # Инициализация базы данных
        logger.info("Initializing database connection...")
        db = Database()

        if not db.test_connection():
            logger.error("Failed to connect to database")
            print("\n❌ Ошибка подключения к PostgreSQL!")
            raise ConnectionError("Не удалось подключиться к базе данных")

        # Создание приложения бота
        application = Application.builder().token(BOT_TOKEN).build()

        # Настройка обработчиков
        setup_handlers(application)

        # Информация о запуске
        print("\n✅ Бот успешно запущен!")
        print("\n📊 Информация:")
        print(f"• База данных: {os.getenv('DATABASE_URL')}")
        print(f"• Режим: Docker контейнер")

        # Статистика базы данных
        stats = db.get_stats()
        if stats:
            print(f"• Сообщений в БД: {stats['messages_count']}")
            print(f"• Пользователей в БД: {stats['users_count']}")

        print("\n📋 Доступные команды:")
        print("  /start - Начать работу")
        print("  /help - Помощь")
        print("  /stats - Статистика")
        print("  /mymessages - Ваши сообщения")

        admin_id = os.getenv('ADMIN_ID')
        if admin_id and admin_id != '0':
            print(f"  /allusers - Все пользователи (админ: {admin_id})")

        print("\n🔄 Для проверки лабораторной:")
        print("  1. Отправьте сообщение боту")
        print("  2. Проверьте /mymessages")
        print("  3. Остановите контейнер: docker-compose down")
        print("  4. Запустите снова: docker-compose up -d")
        print("  5. Убедитесь, что данные сохранились")
        print("=" * 60 + "\n")

        # Запуск бота
        logger.info("Bot polling started")
        application.run_polling(allowed_updates=None)

    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}")
        raise


if __name__ == '__main__':
    main()