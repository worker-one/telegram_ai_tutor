from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    message_text = Column(String)

    user = relationship("User", back_populates="messages")

class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    lang = Column(String)
    last_chat_id = Column(Integer)

    messages = relationship("Message", back_populates="user")
    feedback = relationship("Feedback", back_populates="user")

class Feedback(Base):
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    rating = Column(Integer)
    feedback_text = Column(Text, nullable=True)

    user = relationship("User", back_populates="feedback")
