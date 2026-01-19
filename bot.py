import os
import sys
import logging
from telegram.ext import Application
from dotenv import load_dotenv
from database import Database
from handlers import setup_handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def check_environment():
    """Проверка необходимых переменных окружения"""
    required_vars = ['BOT_TOKEN', 'DATABASE_URL']
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        error_msg = f"Отсутствуют переменные окружения: {', '.join(missing_vars)}"
        logger.error(error_msg)
        print("ОШИБКА КОНФИГУРАЦИИ")
        return False
    return True


def main():
    try:
        # Загрузка переменных окружения
        load_dotenv()

        # Проверка переменных окружения
        if not check_environment():
            sys.exit(1)

        BOT_TOKEN = os.getenv('BOT_TOKEN')

        # Инициализация базы данных
        print("\n Инициализация базы данных...")
        try:
            db = Database()
            if not db.test_connection():
                print("Не удалось подключиться к PostgreSQL")
                sys.exit(1)
            print("Подключение к PostgreSQL успешно")
        except Exception as e:
            print(f"Ошибка инициализации БД: {e}")
            sys.exit(1)

        # Создание приложения бота
        print("Создание Telegram бота...")
        try:
            application = Application.builder().token(BOT_TOKEN).build()
            setup_handlers(application)
            print("Бот инициализирован")
        except Exception as e:
            print(f"Ошибка создания бота: {e}")
            sys.exit(1)

        # Информация о запуске
        print("СИСТЕМА ЗАПУЩЕНА")
        print(f"Администратор: {os.getenv('ADMIN_ID')}")

        # Статистика базы данных
        stats = db.get_stats()
        if stats:
            print("Статистика БД:")
            print(f"   • Сообщений: {stats['messages_count']}")
            print(f"   • Пользователей: {stats['users_count']}")

        admin_id = os.getenv('ADMIN_ID')
        if admin_id and admin_id != '0':
            print(f"   /allusers - Все пользователи (админ)")

        # Запуск бота
        application.run_polling(allowed_updates=None)

    except KeyboardInterrupt:
        print("\n\n Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()