from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from typing import List, Optional

from database import Base, engine, get_db
from models import Student, Recognition, Endorsement, Redemption
from schemas import (
    StudentCreate, StudentResponse,
    RecognitionCreate, RecognitionResponse,
    EndorsementCreate, EndorsementResponse,
    RedemptionCreate, RedemptionResponse,
    LeaderboardEntry
)
from utils import get_current_month_year, check_and_reset_all_credits, should_reset_credits, reset_student_credits

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Boostly API", description="Boost morale, one kudos at a time", version="1.0.0")

# Middleware to check and reset credits on each request
@app.middleware("http")
async def reset_credits_middleware(request, call_next):
    db = next(get_db())
    try:
        check_and_reset_all_credits(db)
    finally:
        db.close()
    response = await call_next(request)
    return response

# ==================== Student Endpoints ====================

@app.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Create a new student"""
    # Check if email already exists
    existing_student = db.query(Student).filter(Student.email == student.email).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student with this email already exists"
        )
    
    new_student = Student(
        name=student.name,
        email=student.email,
        current_balance=100,
        monthly_sending_limit=100,
        last_reset_date=datetime.now()
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get student by ID"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check and reset if needed
    if should_reset_credits(student):
        reset_student_credits(db, student)
    
    return student

@app.get("/students", response_model=List[StudentResponse])
def get_all_students(db: Session = Depends(get_db)):
    """Get all students"""
    students = db.query(Student).all()
    return students

# ==================== Recognition Endpoints ====================

@app.post("/recognitions", response_model=RecognitionResponse, status_code=status.HTTP_201_CREATED)
def create_recognition(
    sender_id: int,
    recognition: RecognitionCreate,
    db: Session = Depends(get_db)
):
    """Create a recognition (sender recognizes receiver with credits)"""
    # Validate sender
    sender = db.query(Student).filter(Student.id == sender_id).first()
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sender not found"
        )
    
    # Check and reset sender credits if needed
    if should_reset_credits(sender):
        reset_student_credits(db, sender)
    
    # Validate receiver
    receiver = db.query(Student).filter(Student.id == recognition.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver not found"
        )
    
    # Business Rules Validation
    # 1. Cannot send to self
    if sender_id == recognition.receiver_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Students cannot send credits to themselves"
        )
    
    # 2. Cannot send more than current balance
    if recognition.credits > sender.current_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Current balance: {sender.current_balance}, requested: {recognition.credits}"
        )
    
    # 3. Check monthly sending limit
    current_month = get_current_month_year()
    monthly_sent = db.query(func.sum(Recognition.credits)).filter(
        and_(
            Recognition.sender_id == sender_id,
            Recognition.month_year == current_month
        )
    ).scalar() or 0
    
    if monthly_sent + recognition.credits > sender.monthly_sending_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Monthly sending limit exceeded. Limit: {sender.monthly_sending_limit}, already sent: {monthly_sent}, requested: {recognition.credits}"
        )
    
    # Create recognition
    new_recognition = Recognition(
        sender_id=sender_id,
        receiver_id=recognition.receiver_id,
        credits=recognition.credits,
        message=recognition.message,
        month_year=current_month
    )
    db.add(new_recognition)
    
    # Update balances
    sender.current_balance -= recognition.credits
    receiver.current_balance += recognition.credits
    
    db.commit()
    db.refresh(new_recognition)
    
    # Get endorsement count
    endorsement_count = db.query(func.count(Endorsement.id)).filter(
        Endorsement.recognition_id == new_recognition.id
    ).scalar() or 0
    
    response = RecognitionResponse(
        id=new_recognition.id,
        sender_id=new_recognition.sender_id,
        receiver_id=new_recognition.receiver_id,
        credits=new_recognition.credits,
        message=new_recognition.message,
        created_at=new_recognition.created_at,
        endorsement_count=endorsement_count
    )
    
    return response

@app.get("/recognitions/{recognition_id}", response_model=RecognitionResponse)
def get_recognition(recognition_id: int, db: Session = Depends(get_db)):
    """Get recognition by ID"""
    recognition = db.query(Recognition).filter(Recognition.id == recognition_id).first()
    if not recognition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recognition not found"
        )
    
    endorsement_count = db.query(func.count(Endorsement.id)).filter(
        Endorsement.recognition_id == recognition_id
    ).scalar() or 0
    
    response = RecognitionResponse(
        id=recognition.id,
        sender_id=recognition.sender_id,
        receiver_id=recognition.receiver_id,
        credits=recognition.credits,
        message=recognition.message,
        created_at=recognition.created_at,
        endorsement_count=endorsement_count
    )
    
    return response

@app.get("/recognitions", response_model=List[RecognitionResponse])
def get_all_recognitions(db: Session = Depends(get_db)):
    """Get all recognitions"""
    recognitions = db.query(Recognition).all()
    result = []
    for rec in recognitions:
        endorsement_count = db.query(func.count(Endorsement.id)).filter(
            Endorsement.recognition_id == rec.id
        ).scalar() or 0
        result.append(RecognitionResponse(
            id=rec.id,
            sender_id=rec.sender_id,
            receiver_id=rec.receiver_id,
            credits=rec.credits,
            message=rec.message,
            created_at=rec.created_at,
            endorsement_count=endorsement_count
        ))
    return result

# ==================== Endorsement Endpoints ====================

@app.post("/endorsements", response_model=EndorsementResponse, status_code=status.HTTP_201_CREATED)
def create_endorsement(
    endorser_id: int,
    endorsement: EndorsementCreate,
    db: Session = Depends(get_db)
):
    """Create an endorsement (like/cheer for a recognition)"""
    # Validate endorser
    endorser = db.query(Student).filter(Student.id == endorser_id).first()
    if not endorser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endorser not found"
        )
    
    # Validate recognition
    recognition = db.query(Recognition).filter(Recognition.id == endorsement.recognition_id).first()
    if not recognition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recognition not found"
        )
    
    # Business Rule: Each endorser can endorse a recognition only once
    existing_endorsement = db.query(Endorsement).filter(
        and_(
            Endorsement.recognition_id == endorsement.recognition_id,
            Endorsement.endorser_id == endorser_id
        )
    ).first()
    
    if existing_endorsement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already endorsed this recognition"
        )
    
    # Create endorsement
    new_endorsement = Endorsement(
        recognition_id=endorsement.recognition_id,
        endorser_id=endorser_id
    )
    db.add(new_endorsement)
    db.commit()
    db.refresh(new_endorsement)
    
    return new_endorsement

@app.get("/endorsements/{endorsement_id}", response_model=EndorsementResponse)
def get_endorsement(endorsement_id: int, db: Session = Depends(get_db)):
    """Get endorsement by ID"""
    endorsement = db.query(Endorsement).filter(Endorsement.id == endorsement_id).first()
    if not endorsement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endorsement not found"
        )
    return endorsement

# ==================== Redemption Endpoints ====================

@app.post("/redemptions", response_model=RedemptionResponse, status_code=status.HTTP_201_CREATED)
def create_redemption(
    student_id: int,
    redemption: RedemptionCreate,
    db: Session = Depends(get_db)
):
    """Redeem credits for voucher (₹5 per credit)"""
    # Validate student
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check and reset if needed
    if should_reset_credits(student):
        reset_student_credits(db, student)
    
    # Business Rules Validation
    # 1. Cannot redeem more than current balance
    if redemption.credits_redeemed > student.current_balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Current balance: {student.current_balance}, requested: {redemption.credits_redeemed}"
        )
    
    # 2. Must redeem at least 1 credit
    if redemption.credits_redeemed <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credits to redeem must be greater than 0"
        )
    
    # Calculate voucher amount (₹5 per credit)
    voucher_amount = redemption.credits_redeemed * 5
    
    # Create redemption
    new_redemption = Redemption(
        student_id=student_id,
        credits_redeemed=redemption.credits_redeemed,
        voucher_amount=voucher_amount
    )
    db.add(new_redemption)
    
    # Permanently deduct credits
    student.current_balance -= redemption.credits_redeemed
    
    db.commit()
    db.refresh(new_redemption)
    
    return new_redemption

@app.get("/redemptions/{redemption_id}", response_model=RedemptionResponse)
def get_redemption(redemption_id: int, db: Session = Depends(get_db)):
    """Get redemption by ID"""
    redemption = db.query(Redemption).filter(Redemption.id == redemption_id).first()
    if not redemption:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Redemption not found"
        )
    return redemption

@app.get("/students/{student_id}/redemptions", response_model=List[RedemptionResponse])
def get_student_redemptions(student_id: int, db: Session = Depends(get_db)):
    """Get all redemptions for a student"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    redemptions = db.query(Redemption).filter(Redemption.student_id == student_id).all()
    return redemptions

# ==================== Leaderboard Endpoint ====================

@app.get("/leaderboard", response_model=List[LeaderboardEntry])
def get_leaderboard(limit: Optional[int] = 10, db: Session = Depends(get_db)):
    """Get leaderboard of top recipients ranked by total credits received"""
    # Query to get total credits received per student
    credits_query = db.query(
        Recognition.receiver_id,
        func.sum(Recognition.credits).label('total_credits')
    ).group_by(Recognition.receiver_id).subquery()
    
    # Query to get total recognitions received per student
    recognitions_query = db.query(
        Recognition.receiver_id,
        func.count(Recognition.id).label('total_recognitions')
    ).group_by(Recognition.receiver_id).subquery()
    
    # Query to get total endorsements received per student (across all their recognitions)
    endorsements_query = db.query(
        Recognition.receiver_id,
        func.count(Endorsement.id).label('total_endorsements')
    ).join(Endorsement, Recognition.id == Endorsement.recognition_id)\
     .group_by(Recognition.receiver_id).subquery()
    
    # Main query joining all data
    leaderboard = db.query(
        Student.id.label('student_id'),
        Student.name.label('student_name'),
        func.coalesce(credits_query.c.total_credits, 0).label('total_credits_received'),
        func.coalesce(recognitions_query.c.total_recognitions, 0).label('total_recognitions_received'),
        func.coalesce(endorsements_query.c.total_endorsements, 0).label('total_endorsements_received')
    ).join(credits_query, Student.id == credits_query.c.receiver_id)\
     .outerjoin(recognitions_query, Student.id == recognitions_query.c.receiver_id)\
     .outerjoin(endorsements_query, Student.id == endorsements_query.c.receiver_id)\
     .order_by(
         func.coalesce(credits_query.c.total_credits, 0).desc(),
         Student.id.asc()
     ).limit(limit).all()
    
    result = []
    for entry in leaderboard:
        result.append(LeaderboardEntry(
            student_id=entry.student_id,
            student_name=entry.student_name,
            total_credits_received=int(entry.total_credits_received),
            total_recognitions_received=int(entry.total_recognitions_received),
            total_endorsements_received=int(entry.total_endorsements_received)
        ))
    
    return result

# ==================== Credit Reset Endpoint (Manual) ====================

@app.post("/credits/reset", status_code=status.HTTP_200_OK)
def manual_reset_credits(db: Session = Depends(get_db)):
    """Manually trigger credit reset for all students (useful for testing)"""
    check_and_reset_all_credits(db)
    return {"message": "Credits reset completed for all eligible students"}

# ==================== Health Check ====================

@app.get("/")
def root():
    """Health check endpoint"""
    return {"message": "Boostly API is running", "version": "1.0.0"}

