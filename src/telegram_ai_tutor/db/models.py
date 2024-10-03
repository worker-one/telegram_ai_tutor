from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    user_id = Column(BigInteger)
    message_text = Column(String)


class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String)
    last_chat_id = Column(Integer)
    language = Column(String, default="en")
