from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan", order_by="Question.order")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"))
    text = Column(Text, nullable=False)
    order = Column(Integer, default=0)

    test = relationship("Test", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)

    question = relationship("Question", back_populates="answers")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    attempts = relationship("TestAttempt", back_populates="user")


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"))
    score = Column(Integer, default=0)
    total = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="attempts")
    test = relationship("Test")


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("test_attempts.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    answer_id = Column(Integer, ForeignKey("answers.id", ondelete="CASCADE"))
    is_correct = Column(Boolean, default=False)
