# Mini Order Management API

A simple FastAPI-based backend for managing users and orders, featuring JWT authentication, background order processing, and SQLite persistence.

## Features

- **User Registration & Login** (JWT authentication)
- **Order Creation, Listing, and Cancellation**
- **Rate Limiting** (via SlowAPI)
- **Background Job Processing** (with APScheduler)
- **SQLite Database** (with SQLAlchemy ORM)
- **CORS Support**
- **Ready for API testing with Postman**

## Getting Started

### Prerequisites

- Python 3.10+
- [pip](https://pip.pypa.io/en/stable/)

### Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/suplexsharma/task-mini-order-api.git
    cd mini-order-api
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables:**
    - Copy `.env.example` to `.env` and adjust as needed.

4. **Run database migrations (optional):**
    ```bash
    python migrate.py
    ```

5. **Start the API server:**
    ```bash
    python main.py
    ```

6. **Access the API docs:**
    - Visit [http://localhost:8000/docs](http://localhost:8000/docs)

### API Endpoints

- `POST /auth/register` — Register a new user
- `POST /auth/login` — Login and get JWT token
- `POST /orders` — Create a new order (authenticated)
- `GET /orders` — List user orders (authenticated)
- `POST /orders/{order_id}/cancel` — Cancel an order (authenticated)
- `GET /health` — Health check

See [`Order-Management-API.postman_collection.json`](Order-Management-API.postman_collection.json) for ready-to-use Postman requests.

### Hardcoded Test User

For convenience, a test user is created automatically:
- **Email:** `test@example.com`
- **Password:** `Password123`

### Background Jobs

Pending orders are processed every 2 minutes via APScheduler.

## Project Structure

```
mini-order-api/
├── auth.py
├── background_jobs.py
├── crud.py
├── database.py
├── frontend.html
├── main.py
├── migrate.py
├── models.py
├── order_management.db
├── requirements.txt
├── schema.sql
├── schemas.py
├── .env.example
└── Order-Management-API.postman_collection.json
```
