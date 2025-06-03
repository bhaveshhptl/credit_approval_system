
# 💳 Credit Approval System - Backend Assignment

A Django-based backend system to handle customer registration, credit scoring, and loan processing. This project is fully containerized using Docker and uses PostgreSQL as the database.

---

## 📦 Features

- Register new customers and assign credit limits
- Calculate credit score based on historical loan data
- Check loan eligibility with interest rate correction
- Process and store new loan applications
- Retrieve individual loan or customer-specific loan history
- Background ingestion of initial customer and loan data from Excel files

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/bhaveshhptl/credit-approval-system.git
cd credit-approval-system
```

### 2. Set Up Environment Variables

Create a `.env` file in the root with the following (or use the one provided):

```env
POSTGRES_DB=credit_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

### 3. Build and Start the Containers

Make sure Docker and Docker Compose are installed, then run:

```bash
docker-compose up --build
```

This will:

- Start Django app
- Set up PostgreSQL
- Load data from `customer_data.xlsx` and `loan_data.xlsx` in the background

> ⚠️ The first run may take a few moments to ingest the Excel files.

---

## 🔍 API Documentation

### `POST /api/register`
Registers a new customer.

#### Request
```json
{
  "first_name": "Ravi",
  "last_name": "Kumar",
  "age": 30,
  "monthly_income": 50000.00,
  "phone_number": "9876543210"
}
```

#### Response
```json
{
  "customer_id": 1,
  "name": "Ravi Kumar",
  "age": 30,
  "monthly_income": 50000.00,
  "approved_limit": 1800000,
  "phone_number": "9876543210"
}
```

---

### `POST /api/check-eligibility`
Checks loan eligibility based on credit score and existing debt.

#### Request
```json
{
  "customer_id": 1,
  "loan_amount": 500000.00,
  "interest_rate": 10.5,
  "tenure": 24
}
```

#### Response
```json
{
  "customer_id": 1,
  "approval": true,
  "interest_rate": 10.5,
  "corrected_interest_rate": 12.0,
  "tenure": 24,
  "monthly_installment": 25000.75
}
```

---

### `POST /api/create-loan`
Processes and creates a loan if the customer is eligible.

#### Request
Same as `/check-eligibility`

#### Response
```json
{
  "loan_id": 101,
  "customer_id": 1,
  "loan_approved": true,
  "message": "Loan approved.",
  "monthly_installment": 25000.75
}
```

---

### `GET /api/view-loan/<loan_id>`
Returns loan and associated customer details.

#### Response
```json
{
  "loan_id": 101,
  "customer": {
    "id": 1,
    "first_name": "Ravi",
    "last_name": "Kumar",
    "phone_number": "9876543210",
    "age": 30
  },
  "loan_amount": 500000.00,
  "interest_rate": 10.5,
  "monthly_installment": 25000.75,
  "tenure": 24
}
```

---

### `GET /api/view-loans/<customer_id>`
Returns a list of all loans for a customer with repayments left.

#### Response
```json
[
  {
    "loan_id": 101,
    "loan_amount": 500000.00,
    "interest_rate": 10.5,
    "monthly_installment": 25000.75,
    "repayments_left": 18
  }
]
```

---

### Video for Proof












https://github.com/user-attachments/assets/03d5a4e9-fde7-4d3c-af2a-4df88382bbae












## 🗃️ Project Structure

```
credit_approval_system/
│
├── api/
│   ├── migrations/
│   ├── __init__.py
│   ├── models.py            # Django models for Customer and Loan
│   ├── serializers.py       # DRF serializers for input/output handling
│   ├── views.py             # API views
│   ├── utils.py             # Credit score & EMI calculators
│   └── urls.py              # API routes
│
├── credit_system/
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # Project-wide URL config
│   └── wsgi.py
│
├── data/
│   ├── customer_data.xlsx       # Initial customer data
│   ├── loan_data.xlsx           # Initial loan data
├── Dockerfile               # App Dockerfile
├── docker-compose.yml       # Docker Compose config
├── manage.py                # Django CLI entry point
└── README.md                # Project documentation
```

---

## 🛠️ Tech Stack

- **Python 3.11**
- **Django 4.x**
- **Django REST Framework**
- **PostgreSQL**
- **Docker & Docker Compose**

---

## 📌 Notes

- Initial data is ingested automatically using background workers at startup.
- Loans are evaluated using custom credit score logic based on repayment history, loan volume, and current EMI burden.
- Monthly installments are computed using compound interest.

---

