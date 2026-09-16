# Smart Inventory & Stock Replenishment Platform

A production-style Python web application backend designed to support real-time inventory management, automated stock replenishment, and demand forecasting.

This repository currently implements:
- **Phase 1: Project Foundation & Backend Setup**
- **Phase 2: Authentication & Role-Based Access Control (RBAC)**
- **Phase 3: Product, Category & Supplier Management**
- **Phase 4: Inventory & Stock Management**

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
│   │       ├── 0001_create_users_table.py
│   │       ├── 0002_create_categories_suppliers_products.py
│   │       └── 0003_create_inventory_tables.py
│   ├── alembic.ini                     # Alembic configuration file
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI entrypoint & router registration
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
│   │   │   ├── user.py                 # User model & UserRole enum
│   │   │   ├── category.py             # Category model
│   │   │   ├── supplier.py             # Supplier model
│   │   │   ├── product.py              # Product model
│   │   │   ├── inventory.py            # Inventory stock model
│   │   │   └── inventory_transaction.py # TransactionType & InventoryTransaction model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py             # Schema exports
│   │   │   ├── user.py                 # User schemas & auth tokens
│   │   │   ├── category.py             # Category schemas
│   │   │   ├── supplier.py             # Supplier schemas
│   │   │   ├── product.py              # Product schemas
│   │   │   ├── inventory.py            # Inventory & InventoryStatus schemas
│   │   │   └── inventory_transaction.py # Stock operation & transaction schemas
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                 # get_current_user & require_roles dependencies
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py             # POST /auth/register, POST /auth/login
│   │   │       ├── users.py            # GET /users/me, GET /users/admin-test
│   │   │       ├── categories.py       # Category CRUD endpoints
│   │   │       ├── suppliers.py        # Supplier CRUD endpoints
│   │   │       ├── products.py         # Product CRUD endpoints
│   │   │       └── inventory.py        # Stock in/out/adjust & history endpoints
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py         # Authentication & registration logic
│   │       ├── category_service.py     # Category business logic & validation
│   │       ├── supplier_service.py     # Supplier business logic & validation
│   │       ├── product_service.py      # Product business logic, FK checks & validation
│   │       └── inventory_service.py    # Atomic stock mutations & transaction ledger
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Shared in-memory test DB & fixtures
│   │   ├── test_auth.py                # Phase 2 test suite (9 tests)
│   │   ├── test_phase3.py              # Phase 3 comprehensive test suite (42 tests)
│   │   └── test_phase4.py              # Phase 4 comprehensive test suite (31 tests / 55 checks)
│   │
│   ├── .env.example                    # Environment variable template
│   ├── .gitignore                      # Git ignore rules for backend
│   └── requirements.txt                # Project dependencies
│
└── README.md                           # Project documentation
```

---

## Role-Based Access Control (RBAC)

The platform supports three distinct roles with clearly delineated responsibilities:

| Entity / Resource | ADMIN | INVENTORY_MANAGER | WAREHOUSE_STAFF |
| :--- | :--- | :--- | :--- |
| **System Admin Test** (`/users/admin-test`) | Full Access | Forbidden (403) | Forbidden (403) |
| **Categories** (`POST`, `PUT`, `DELETE`) | Allowed | Allowed | Forbidden (403) |
| **Categories** (`GET`) | Allowed | Allowed | Read-Only |
| **Suppliers** (`POST`, `PUT`, `DELETE`) | Allowed | Allowed | Forbidden (403) |
| **Suppliers** (`GET`) | Allowed | Allowed | Read-Only |
| **Products** (`POST`, `PUT`, `DELETE`) | Allowed | Allowed | Forbidden (403) |
| **Products** (`GET`) | Allowed | Allowed | Read-Only |
| **Stock In / Stock Out** (`POST /inventory/stock-*`) | Allowed | Allowed | Allowed |
| **Stock Adjustment** (`POST /inventory/adjustment`) | Allowed | Allowed | Forbidden (403) |
| **Inventory & History Read** (`GET /inventory/*`) | Allowed | Allowed | Read-Only |

---

## Setup & Execution

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- **PostgreSQL 14+** installed and running

### 2. Environment Setup
```bash
cd backend
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configuration & Database Migrations
Copy `.env.example` to `.env` and set your credentials:
```bash
cp .env.example .env
```

Apply database migrations:
```bash
alembic upgrade head
```

### 4. Running the Server
```bash
uvicorn app.main:app --reload
```
API is accessible at `http://127.0.0.1:8000`.

---

## API Endpoints Summary

### System Endpoints (Phase 1)
- `GET /` — Service confirmation message
- `GET /health` — Service health status

### Authentication Endpoints (Phase 2)
- `POST /auth/register` — Register a new user (`UserResponse` excludes password and hash)
- `POST /auth/login` — Authenticate credentials and receive Bearer JWT
- `GET /users/me` — Current authenticated user profile
- `GET /users/admin-test` — Admin-only verification test

### Category Endpoints (Phase 3)
- `POST /categories` — Create category (requires `ADMIN` or `INVENTORY_MANAGER`)
- `GET /categories` — List categories (supports `?is_active=true/false`)
- `GET /categories/{category_id}` — Retrieve single category
- `PUT /categories/{category_id}` — Update category details
- `DELETE /categories/{category_id}` — Deactivate category (blocked if referenced by products)

### Supplier Endpoints (Phase 3)
- `POST /suppliers` — Register supplier (requires `ADMIN` or `INVENTORY_MANAGER`)
- `GET /suppliers` — List suppliers (supports `?is_active=true/false`)
- `GET /suppliers/{supplier_id}` — Retrieve single supplier
- `PUT /suppliers/{supplier_id}` — Update supplier details
- `DELETE /suppliers/{supplier_id}` — Deactivate supplier (blocked if referenced by products)

### Product Endpoints (Phase 3)
- `POST /products` — Create product (requires active category, active supplier, unique SKU)
- `GET /products` — List products (supports `?category_id=`, `?supplier_id=`, `?is_active=`, `?search=`, `?sku=`)
- `GET /products/{product_id}` — Retrieve single product
- `PUT /products/{product_id}` — Update product specifications
- `DELETE /products/{product_id}` — Soft-deactivate product (`is_active = False`)

### Inventory & Stock Endpoints (Phase 4)
- `POST /inventory/stock-in` — Inbound stock reception (creates `STOCK_IN` transaction, updates stock atomically)
- `POST /inventory/stock-out` — Outbound stock dispatch (checks `available_stock`, creates `STOCK_OUT` transaction)
- `POST /inventory/adjustment` — Stock adjustment (`ADJUSTMENT_IN` / `ADJUSTMENT_OUT`, mandatory reason, `ADMIN`/`INVENTORY_MANAGER` only)
- `GET /inventory` — Query inventory items with filters (`?low_stock=true`, `?status=`, `?category_id=`)
- `GET /inventory/{product_id}` — Current inventory for a specific product
- `GET /inventory/transactions` — Transaction history with filters (`?product_id=`, `?transaction_type=`, `?user_id=`, `?start_date=`, `?end_date=`)
- `GET /inventory/transactions/{transaction_id}` — Retrieve single transaction audit record (strictly immutable; no `PUT`/`DELETE` endpoints)

---

## Interactive Documentation & Swagger Testing

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

Protected routes use Bearer token authentication. Click the green **Authorize** button in Swagger UI and input your access token to test endpoints directly.

---

## Running the Automated Test Suite

Run the full unified test suite across all phases (Phase 2 Auth, Phase 3 Catalog, and Phase 4 Inventory):

```bash
pytest tests/test_auth.py tests/test_phase3.py tests/test_phase4.py -v
```

Or run Phase 4 inventory tests individually:

```bash
pytest tests/test_phase4.py -v
```
