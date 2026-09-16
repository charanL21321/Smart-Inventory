# Smart Inventory & Stock Replenishment Platform

A production-style Python web application backend designed to support real-time inventory management, automated stock replenishment, and demand forecasting.

This repository currently implements:
- **Phase 1: Project Foundation & Backend Setup**
- **Phase 2: Authentication & Role-Based Access Control (RBAC)**

---

## Technology Stack

- **Backend Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **ASGI Web Server:** [Uvicorn](https://www.uvicorn.org/)
- **ORM / Database Layer:** [SQLAlchemy 2.x](https://www.sqlalchemy.org/)
- **Database Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
- **PostgreSQL Driver:** [psycopg2-binary](https://www.psycopg.org/)
- **Authentication & Security:**
  - Password Hashing: [bcrypt](https://pypi.org/project/bcrypt/) via [Passlib](https://passlib.readthedocs.io/)
  - Token Management: [python-jose](https://github.com/mpdavis/python-jose) (Cryptographic JWT)
- **Settings & Schema Validation:** [Pydantic v2](https://docs.pydantic.dev/) & [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- **Configuration Management:** `.env` environment files via `python-dotenv`
- **Testing:** [pytest](https://docs.pytest.org/) & [httpx](https://www.python-httpx.org/)
- **Dependency Management:** `requirements.txt`
- **Version Control:** Git

---

## Project Structure

```
smart-inventory-platform/
│
├── backend/
│   ├── alembic/                        # Alembic migration environment and versions
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_create_users_table.py
│   ├── alembic.ini                     # Alembic configuration file
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application entrypoint & lifecycle
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Pydantic Settings & environment variables
│   │   │   └── security.py             # Password hashing (bcrypt) & JWT operations
│   │   │
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py           # Engine, SessionLocal, get_db, connection check
│   │   │   └── base.py                 # SQLAlchemy 2.x Declarative Base
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py             # Model exports
│   │   │   └── user.py                 # User SQLAlchemy model & UserRole enum
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py             # Schema exports
│   │   │   └── user.py                 # UserCreate, UserResponse, LoginRequest, Token
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                 # get_current_user & require_roles dependencies
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py             # POST /auth/register, POST /auth/login
│   │   │       └── users.py            # GET /users/me, GET /users/admin-test
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       └── auth_service.py         # Registration & authentication business logic
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_auth.py                # Phase 2 test suite
│   │
│   ├── .env.example                    # Environment variable template
│   ├── .gitignore                      # Git ignore rules for backend
│   └── requirements.txt                # Phase 1 & 2 dependencies
│
└── README.md                           # Project documentation
```

---

## Roles & Permissions

The platform defines three controlled user roles:

1. **`ADMIN`**: Full system access, administrative controls, and system configuration.
2. **`INVENTORY_MANAGER`**: Inventory management, supplier management, purchase orders, and stock analytics.
3. **`WAREHOUSE_STAFF`**: Operational stock adjustments, stock-in, stock-out, and physical inventory handling.

Role authorization is implemented as a reusable dependency:
```python
from app.api.deps import require_roles
from app.models.user import UserRole

@router.get("/protected")
def sensitive_endpoint(current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER))):
    ...
```

---

## Setup Instructions

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- **PostgreSQL 14+** installed and running

### 2. Create and Activate Virtual Environment

Navigate to the `backend/` directory:

```bash
cd backend
```

Create a virtual environment:

- **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configuration

1. Copy `.env.example` to create your local `.env` file:
   ```bash
   # Windows PowerShell:
   Copy-Item .env.example .env

   # macOS / Linux:
   cp .env.example .env
   ```

2. Open `backend/.env` and update with your PostgreSQL credentials and JWT secret key:
   ```ini
   APP_NAME=Smart Inventory & Stock Replenishment Platform
   APP_VERSION=1.0.0
   DEBUG=True
   DATABASE_URL=postgresql+psycopg2://<username>:<password>@localhost:5432/smart_inventory
   CHECK_DB_ON_STARTUP=False

   JWT_SECRET_KEY=generate-a-strong-random-secret-key-32-chars-min
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

---

## Running the Application

Start the development server with Uvicorn from inside `backend/`:

```bash
uvicorn app.main:app --reload
```

The application is available at `http://127.0.0.1:8000`.

---

## API Endpoints

### System Endpoints (Phase 1)
- `GET /`: API status confirmation
- `GET /health`: Health check endpoint

### Authentication Endpoints (Phase 2)
- `POST /auth/register`:
  - **Payload:** `{"username": "...", "email": "...", "password": "...", "full_name": "...", "role": "WAREHOUSE_STAFF"}`
  - **Response:** `201 Created` with public profile (password and hash are NEVER returned).
- `POST /auth/login`:
  - **Payload:** `{"username": "<username or email>", "password": "..."}`
  - **Response:** `200 OK` with `{"access_token": "...", "token_type": "bearer"}`.

### Protected User Endpoints (Phase 2)
- `GET /users/me`:
  - Requires Bearer token header (`Authorization: Bearer <token>`).
  - Returns authenticated user profile.
- `GET /users/admin-test`:
  - Requires Bearer token of a user with role `ADMIN`.
  - Rejects other roles with `403 Forbidden`.

---

## Interactive Documentation & Swagger Testing

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Testing Authentication in Swagger UI:
1. Open `/docs` in your browser.
2. Call `POST /auth/register` to create a user account.
3. Call `POST /auth/login` with your credentials to obtain the `access_token`.
4. Click the green **Authorize** button at the top right of Swagger UI.
5. Enter the `access_token` into the **Value** field and click **Authorize**.
6. Call `GET /users/me` — it will return your user details.
7. Call `GET /users/admin-test` to test role-based access control.

---

## Running Automated Tests

Run the test suite from the `backend/` directory:

```bash
pytest tests/test_auth.py -v
```
