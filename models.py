from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import expression

Base = declarative_base()


class Message(Base):
    """
    Модель для хранения сообщений пользователей.
    Сохраняет все текстовые сообщения, отправленные боту.
    """
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='Уникальный идентификатор сообщения')
    user_id = Column(BigInteger, nullable=False, comment='ID пользователя Telegram')
    username = Column(String(100), nullable=True, comment='Имя пользователя Telegram (если есть)')
    first_name = Column(String(100), nullable=True, comment='Имя пользователя')
    last_name = Column(String(100), nullable=True, comment='Фамилия пользователя')
    message_text = Column(Text, nullable=False, comment='Текст сообщения')
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                        comment='Время получения сообщения')

    def __repr__(self):
        return f"<Message(id={self.id}, user_id={self.user_id}, text='{self.message_text[:20]}...')>"

    def to_dict(self):
        """Конвертация объекта в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'message_text': self.message_text,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class User(Base):
    """
    Модель для хранения информации о пользователях.
    Содержит основную информацию и время последней активности.
    """
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True, comment='ID пользователя Telegram (первичный ключ)')
    username = Column(String(100), nullable=True, comment='Имя пользователя Telegram')
    first_name = Column(String(100), nullable=True, comment='Имя пользователя')
    last_name = Column(String(100), nullable=True, comment='Фамилия пользователя')
    created_at = Column(DateTime(timezone=True), server_default=func.now(),
                        comment='Время первой регистрации пользователя')
    last_seen = Column(DateTime(timezone=True), server_default=func.now(),
                       onupdate=func.now(), comment='Время последней активности')

    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}', first_name='{self.first_name}')>"

    def to_dict(self):
        """Конвертация объекта в словарь"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }

    def update_last_seen(self):
        """Обновление времени последней активности"""
        self.last_seen = func.now()


# Создание индексов для оптимизации запросов
# Это можно сделать здесь или в database.py при создании таблиц
Index('idx_messages_user_id', Message.user_id)
Index('idx_messages_created_at', Message.created_at)
Index('idx_users_last_seen', User.last_seen)