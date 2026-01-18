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
    """Класс для работы с базой данных"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Инициализация подключения к базе данных"""
        if not hasattr(self, 'initialized'):
            self._initialize()
            self.initialized = True

    def _initialize(self):
        """Инициализация подключения к базе данных"""
        database_url = os.getenv('DATABASE_URL')

        if not database_url:
            logger.error("DATABASE_URL not found in environment variables")
            raise ValueError("DATABASE_URL не найден в переменных окружения")

        logger.info(f"Connecting to database: {database_url}")

        try:
            # Подключение к базе данных с увеличенным таймаутом
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                echo=False,
                pool_size=5,
                max_overflow=10,
                connect_args={
                    'connect_timeout': 10,
                    'application_name': 'telegram_bot'
                }
            )

            # Проверка подключения
            self._test_connection()

            # Создание таблиц, если они не существуют
            self._create_tables()

            # Создание сессии
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )

            logger.info("Database connection successful")

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            print(f"\n❌ Ошибка подключения к PostgreSQL!")
            print(f"URL: {database_url}")
            print("Убедитесь, что:")
            print("1. PostgreSQL запущен на порту 5433")
            print("2. База данных 'postgres' существует")
            print("3. Пользователь 'postgres' имеет доступ")
            raise

    def _test_connection(self):
        """Тестирование подключения"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info(f"PostgreSQL version: {version}")

                # Проверяем существование таблиц
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'messages'
                    );
                """))
                tables_exist = result.fetchone()[0]

                if not tables_exist:
                    logger.info("Tables don't exist, will be created")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise

    def _create_tables(self):
        """Создание таблиц"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def get_session(self):
        """Получение сессии базы данных"""
        return self.SessionLocal()

    def close_session(self):
        """Закрытие сессии"""
        if hasattr(self, 'SessionLocal'):
            self.SessionLocal.remove()

    def test_connection(self):
        """Тестирование подключения к базе данных"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection error: {e}")
            return False

    def get_stats(self):
        """Получение статистики базы данных"""
        session = self.get_session()
        try:
            messages_count = session.query(Message).count()
            users_count = session.query(User).count()
            last_message = session.query(Message).order_by(Message.created_at.desc()).first()

            return {
                'messages_count': messages_count,
                'users_count': users_count,
                'last_message_time': last_message.created_at if last_message else None
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return None
        finally:
            session.close()