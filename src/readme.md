# Boostly API - Project Documentation

## Overview

Boostly is a platform that enables college students to recognize their peers, allocate monthly credits, and redeem earned rewards. The application encourages appreciation and engagement across student communities.

## Technology Stack

- **Framework**: FastAPI (Python)
- **Database**: SQLite (can be easily switched to PostgreSQL/MySQL)
- **ORM**: SQLAlchemy
- **Validation**: Pydantic

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps

1. **Navigate to the src directory**:
   ```bash
   cd src
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

   The API will be available at: `http://localhost:8000`

5. **Access API documentation**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Database

The application uses SQLite by default. The database file (`boostly.db`) will be automatically created in the `src/` directory when you first run the application.

### Database Schema

- **students**: Stores student information and credit balances
- **recognitions**: Stores recognition transactions between students
- **endorsements**: Stores endorsements (likes) on recognitions
- **redemptions**: Stores credit redemption transactions

## API Endpoints

### Health Check

#### GET `/`
Check if the API is running.

**Response**:
```json
{
  "message": "Boostly API is running",
  "version": "1.0.0"
}
```

---

### Student Endpoints

#### POST `/students`
Create a new student.

**Request Body**:
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "current_balance": 100,
  "monthly_sending_limit": 100
}
```

#### GET `/students/{student_id}`
Get student by ID.

**Response** (200 OK):
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john.doe@example.com",
  "current_balance": 100,
  "monthly_sending_limit": 100
}
```

#### GET `/students`
Get all students.

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "current_balance": 100,
    "monthly_sending_limit": 100
  }
]
```

---

### Recognition Endpoints

#### POST `/recognitions?sender_id={sender_id}`
Create a recognition (transfer credits from sender to receiver).

**Query Parameters**:
- `sender_id` (required): ID of the student sending credits

**Request Body**:
```json
{
  "receiver_id": 2,
  "credits": 20,
  "message": "Great work on the project!"
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "sender_id": 1,
  "receiver_id": 2,
  "credits": 20,
  "message": "Great work on the project!",
  "created_at": "2024-01-15T10:30:00",
  "endorsement_count": 0
}
```

**Business Rules**:
- Students cannot send credits to themselves
- Cannot send more credits than current balance
- Cannot exceed monthly sending limit (100 credits per month)
- Each student receives 100 credits every month (resets at start of calendar month)

#### GET `/recognitions/{recognition_id}`
Get recognition by ID.

**Response** (200 OK):
```json
{
  "id": 1,
  "sender_id": 1,
  "receiver_id": 2,
  "credits": 20,
  "message": "Great work on the project!",
  "created_at": "2024-01-15T10:30:00",
  "endorsement_count": 3
}
```

#### GET `/recognitions`
Get all recognitions.

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "sender_id": 1,
    "receiver_id": 2,
    "credits": 20,
    "message": "Great work on the project!",
    "created_at": "2024-01-15T10:30:00",
    "endorsement_count": 3
  }
]
```

---

### Endorsement Endpoints

#### POST `/endorsements?endorser_id={endorser_id}`
Create an endorsement (like/cheer for a recognition).

**Query Parameters**:
- `endorser_id` (required): ID of the student endorsing

**Request Body**:
```json
{
  "recognition_id": 1
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "recognition_id": 1,
  "endorser_id": 3,
  "created_at": "2024-01-15T11:00:00"
}
```

**Business Rules**:
- Each endorser can endorse a recognition only once
- Endorsements don't affect credit balances

#### GET `/endorsements/{endorsement_id}`
Get endorsement by ID.

**Response** (200 OK):
```json
{
  "id": 1,
  "recognition_id": 1,
  "endorser_id": 3,
  "created_at": "2024-01-15T11:00:00"
}
```

---

### Redemption Endpoints

#### POST `/redemptions?student_id={student_id}`
Redeem credits for voucher (₹5 per credit).

**Query Parameters**:
- `student_id` (required): ID of the student redeeming

**Request Body**:
```json
{
  "credits_redeemed": 50
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "student_id": 2,
  "credits_redeemed": 50,
  "voucher_amount": 250,
  "created_at": "2024-01-15T12:00:00"
}
```

**Business Rules**:
- Credits are converted at ₹5 per credit
- Credits are permanently deducted from balance
- Can only redeem credits that have been received

#### GET `/redemptions/{redemption_id}`
Get redemption by ID.

**Response** (200 OK):
```json
{
  "id": 1,
  "student_id": 2,
  "credits_redeemed": 50,
  "voucher_amount": 250,
  "created_at": "2024-01-15T12:00:00"
}
```

#### GET `/students/{student_id}/redemptions`
Get all redemptions for a student.

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "student_id": 2,
    "credits_redeemed": 50,
    "voucher_amount": 250,
    "created_at": "2024-01-15T12:00:00"
  }
]
```

---

### Leaderboard Endpoint

#### GET `/leaderboard?limit={limit}`
Get leaderboard of top recipients ranked by total credits received.

**Query Parameters**:
- `limit` (optional): Number of top students to return (default: 10)

**Response** (200 OK):
```json
[
  {
    "student_id": 2,
    "student_name": "Jane Smith",
    "total_credits_received": 150,
    "total_recognitions_received": 5,
    "total_endorsements_received": 12
  },
  {
    "student_id": 3,
    "student_name": "Bob Johnson",
    "total_credits_received": 120,
    "total_recognitions_received": 4,
    "total_endorsements_received": 8
  }
]
```

**Business Rules**:
- Ranked by total credits received (descending)
- If same credits, ranked by student ID (ascending)
- Includes total recognitions and endorsements received

---

### Credit Reset Endpoint

#### POST `/credits/reset`
Manually trigger credit reset for all students (useful for testing).

**Response** (200 OK):
```json
{
  "message": "Credits reset completed for all eligible students"
}
```

**Note**: Credits are automatically reset at the start of each calendar month. This endpoint is for manual testing.

---

## Sample Requests (cURL)

### Create a Student
```bash
curl -X POST "http://localhost:8000/students" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com"
  }'
```

### Create a Recognition
```bash
curl -X POST "http://localhost:8000/recognitions?sender_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_id": 2,
    "credits": 20,
    "message": "Great work!"
  }'
```

### Create an Endorsement
```bash
curl -X POST "http://localhost:8000/endorsements?endorser_id=3" \
  -H "Content-Type: application/json" \
  -d '{
    "recognition_id": 1
  }'
```

### Redeem Credits
```bash
curl -X POST "http://localhost:8000/redemptions?student_id=2" \
  -H "Content-Type: application/json" \
  -d '{
    "credits_redeemed": 50
  }'
```

### Get Leaderboard
```bash
curl -X GET "http://localhost:8000/leaderboard?limit=5"
```

---

## Credit Reset Mechanism

The application automatically resets credits at the start of each calendar month:

- Each student's available credits reset to **100** at the start of each calendar month
- Up to **50 unused credits** from the previous month can be carried forward
- If a student has more than 50 unused credits, only 50 can be carried forward
- The monthly sending limit also resets to **100 credits**

The reset is checked automatically on each API request via middleware. If a student's last reset date is in a previous month, their credits are automatically reset.

---

## Error Responses

All endpoints return appropriate HTTP status codes:

- **200 OK**: Successful GET request
- **201 Created**: Successful POST request (resource created)
- **400 Bad Request**: Validation error or business rule violation
- **404 Not Found**: Resource not found

**Example Error Response**:
```json
{
  "detail": "Insufficient balance. Current balance: 50, requested: 100"
}
```

---

## Project Structure

```
src/
├── main.py              # FastAPI application and endpoints
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic request/response schemas
├── database.py          # Database configuration
├── utils.py             # Utility functions (credit reset logic)
├── requirements.txt     # Python dependencies
└── readme.md           # This file
```

---

## Notes

- The database file (`boostly.db`) is created automatically in the `src/` directory
- All timestamps are in UTC
- Credit reset happens automatically via middleware on each request
- Monthly limits are tracked using `YYYY-MM` format
