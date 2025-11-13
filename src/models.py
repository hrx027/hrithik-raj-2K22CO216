from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    current_balance = Column(Integer, default=100, nullable=False)
    monthly_sending_limit = Column(Integer, default=100, nullable=False)
    last_reset_date = Column(DateTime, default=datetime.now)
    
    # Relationships
    sent_recognitions = relationship("Recognition", foreign_keys="Recognition.sender_id", back_populates="sender")
    received_recognitions = relationship("Recognition", foreign_keys="Recognition.receiver_id", back_populates="receiver")
    redemptions = relationship("Redemption", back_populates="student")
    
    __table_args__ = (
        CheckConstraint('current_balance >= 0', name='check_balance_non_negative'),
        CheckConstraint('monthly_sending_limit >= 0', name='check_sending_limit_non_negative'),
    )

class Recognition(Base):
    __tablename__ = "recognitions"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    credits = Column(Integer, nullable=False)
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    month_year = Column(String, nullable=False)  # Format: "YYYY-MM" for tracking monthly limits
    
    # Relationships
    sender = relationship("Student", foreign_keys=[sender_id], back_populates="sent_recognitions")
    receiver = relationship("Student", foreign_keys=[receiver_id], back_populates="received_recognitions")
    endorsements = relationship("Endorsement", back_populates="recognition", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('credits > 0', name='check_credits_positive'),
        CheckConstraint('sender_id != receiver_id', name='check_no_self_recognition'),
    )

class Endorsement(Base):
    __tablename__ = "endorsements"
    
    id = Column(Integer, primary_key=True, index=True)
    recognition_id = Column(Integer, ForeignKey("recognitions.id"), nullable=False)
    endorser_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    recognition = relationship("Recognition", back_populates="endorsements")
    
    __table_args__ = (
        UniqueConstraint('recognition_id', 'endorser_id', name='unique_endorsement'),
    )

class Redemption(Base):
    __tablename__ = "redemptions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    credits_redeemed = Column(Integer, nullable=False)
    voucher_amount = Column(Integer, nullable=False)  # In rupees (credits * 5)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    student = relationship("Student", back_populates="redemptions")
    
    __table_args__ = (
        CheckConstraint('credits_redeemed > 0', name='check_redemption_positive'),
    )

