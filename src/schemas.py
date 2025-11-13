from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Student Schemas
class StudentCreate(BaseModel):
    name: str
    email: EmailStr

class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    current_balance: int
    monthly_sending_limit: int
    
    class Config:
        from_attributes = True

# Recognition Schemas
class RecognitionCreate(BaseModel):
    receiver_id: int
    credits: int
    message: Optional[str] = None

class RecognitionResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    credits: int
    message: Optional[str]
    created_at: datetime
    endorsement_count: int = 0
    
    class Config:
        from_attributes = True

# Endorsement Schemas
class EndorsementCreate(BaseModel):
    recognition_id: int

class EndorsementResponse(BaseModel):
    id: int
    recognition_id: int
    endorser_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Redemption Schemas
class RedemptionCreate(BaseModel):
    credits_redeemed: int

class RedemptionResponse(BaseModel):
    id: int
    student_id: int
    credits_redeemed: int
    voucher_amount: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Leaderboard Schemas
class LeaderboardEntry(BaseModel):
    student_id: int
    student_name: str
    total_credits_received: int
    total_recognitions_received: int
    total_endorsements_received: int

