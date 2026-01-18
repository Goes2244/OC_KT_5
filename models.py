from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Message(Base):
    """Модель для хранения сообщений пользователей"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    """Модель для хранения информации о пользователях"""
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}')>"