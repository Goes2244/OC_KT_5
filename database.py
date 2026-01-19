import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from models import Base, Message, User

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()


class Database:
    """Класс для управления подключением к базе данных"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Инициализация подключения к базе данных"""
        # Сначала пробуем получить из переменных окружения
        database_url = os.getenv('DATABASE_URL')

        # Если не нашли, используем значение по умолчанию для Docker
        if not database_url:
            database_url = "postgresql://bot_user:bot_password@postgres:5432/telegram_bot_db"
            logger.info(f"DATABASE_URL не найден в .env, используется значение по умолчанию для Docker")

        logger.info(f"Подключение к базе данных: {database_url}")

        try:
            # Создание движка SQLAlchemy
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                echo=False,
                pool_size=5,
                max_overflow=10
            )

            # Тестирование подключения
            self._test_connection()

            # Создание таблиц
            self._create_tables()

            # Создание фабрики сессий
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )

            logger.info("✅ Подключение к базе данных успешно установлено")

        except Exception as e:
            logger.error(f" Ошибка подключения к базе данных: {e}")
            print(f"\n ОШИБКА ПОДКЛЮЧЕНИЯ К POSTGRESQL")
            print(f"URL: {database_url}")
            raise

    def _test_connection(self):
        try:
            with self.engine.connect() as conn:
                # Получаем версию PostgreSQL
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"PostgreSQL версия: {version.split(',')[0]}")

                # Проверяем существование нашей базы данных
                result = conn.execute(text("SELECT current_database()"))
                db_name = result.fetchone()[0]
                logger.info(f"База данных: {db_name}")

                # Проверяем существование таблиц
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'messages'
                    );
                """))
                tables_exist = result.fetchone()[0]

                if tables_exist:
                    logger.info("Таблицы уже существуют")
                else:
                    logger.info("Таблицы будут созданы")

        except Exception as e:
            logger.error(f"Тест подключения не пройден: {e}")
            raise

    def _create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Таблицы базы данных созданы/проверены")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise

    def get_session(self):
        """Получение новой сессии базы данных"""
        return self.SessionLocal()

    def close_session(self):
        """Закрытие сессии (для cleanup)"""
        if hasattr(self, 'SessionLocal'):
            self.SessionLocal.remove()

    def test_connection(self):
        """Простой тест подключения (используется при запуске)"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Тест подключения провален: {e}")
            return False

    def get_stats(self):
        """Получение статистики базы данных"""
        session = self.get_session()
        try:
            messages_count = session.query(Message).count()
            users_count = session.query(User).count()

            # Получаем последнее сообщение
            last_message = session.query(Message).order_by(Message.created_at.desc()).first()

            return {
                'messages_count': messages_count,
                'users_count': users_count,
                'last_message_time': last_message.created_at if last_message else None,
                'last_message_user': last_message.user_id if last_message else None
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return None
        finally:
            session.close()

    def get_user_messages(self, user_id, limit=10):
        """Получение сообщений пользователя"""
        session = self.get_session()
        try:
            messages = session.query(Message) \
                .filter_by(user_id=user_id) \
                .order_by(Message.created_at.desc()) \
                .limit(limit) \
                .all()
            return messages
        except Exception as e:
            logger.error(f"Ошибка получения сообщений пользователя: {e}")
            return []
        finally:
            session.close()

    def __del__(self):
        """Деструктор - закрываем соединения"""
        self.close_session()