from datetime import datetime
from sqlalchemy.orm import Session
from models import Student

def get_current_month_year() -> str:
    """Get current month-year string in YYYY-MM format"""
    return datetime.now().strftime("%Y-%m")

def should_reset_credits(student: Student) -> bool:
    """Check if student's credits should be reset based on last reset date"""
    current_date = datetime.now()
    last_reset = student.last_reset_date
    
    # Check if we're in a different month
    if current_date.year > last_reset.year or \
       (current_date.year == last_reset.year and current_date.month > last_reset.month):
        return True
    return False

def reset_student_credits(db: Session, student: Student):
    """Reset student credits with carry-forward logic"""
    # Calculate carry-forward (max 50 credits)
    unused_credits = student.current_balance
    carry_forward = min(unused_credits, 50)
    
    # Reset to 100 + carry_forward
    student.current_balance = 100 + carry_forward
    student.monthly_sending_limit = 100
    student.last_reset_date = datetime.now()
    
    db.commit()
    db.refresh(student)

def check_and_reset_all_credits(db: Session):
    """Check all students and reset credits if needed"""
    students = db.query(Student).all()
    for student in students:
        if should_reset_credits(student):
            reset_student_credits(db, student)

