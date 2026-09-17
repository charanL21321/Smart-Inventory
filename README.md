# Smart Inventory & Stock Replenishment Platform

A production-style Python web application backend designed to support real-time inventory management, automated stock replenishment, and demand forecasting.

This repository currently implements:
- **Phase 1: Project Foundation & Backend Setup**
- **Phase 2: Authentication & Role-Based Access Control (RBAC)**
- **Phase 3: Product, Category & Supplier Management**
- **Phase 4: Inventory & Stock Management**
- **Phase 5: Sales & Purchase Order Management**
- **Phase 6: Smart Replenishment Engine**
- **Phase 7: Demand Analysis & Forecasting**
- **Phase 8: React Frontend & Dashboard**

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
│   │       ├── 0003_create_inventory_tables.py
│   │       ├── 0004_create_sales_purchase_orders.py
│   │       ├── 0005_create_replenishment_recommendations.py
│   │       └── 0006_create_demand_forecasts.py
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
│   │   │   ├── inventory_transaction.py # TransactionType & InventoryTransaction model
│   │   │   ├── sale.py                 # Sale model (immutable ledger)
│   │   │   ├── purchase_order.py       # PurchaseOrder model & PurchaseOrderStatus enum
│   │   │   ├── purchase_order_item.py  # PurchaseOrderItem model
│   │   │   ├── replenishment_recommendation.py # ReplenishmentRecommendation model & enums
│   │   │   └── demand_forecast.py      # DemandForecast, DemandForecastValue & enums
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py             # Schema exports
│   │   │   ├── user.py                 # User schemas & auth tokens
│   │   │   ├── category.py             # Category schemas
│   │   │   ├── supplier.py             # Supplier schemas
│   │   │   ├── product.py              # Product schemas
│   │   │   ├── inventory.py            # Inventory & InventoryStatus schemas
│   │   │   ├── inventory_transaction.py # Stock operation & transaction schemas
│   │   │   ├── sale.py                 # Sale request and response schemas
│   │   │   ├── purchase_order.py       # PO, items, status, and receipt schemas
│   │   │   ├── replenishment.py        # Recommendation response and dismiss schemas
│   │   │   └── forecast.py             # Demand forecasting schemas & enums
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
│   │   │       ├── inventory.py        # Stock in/out/adjust & history endpoints
│   │   │       ├── sales.py            # Sales recording & history endpoints
│   │   │       ├── purchase_orders.py  # Purchase order lifecycle & receiving endpoints
│   │   │       ├── replenishment.py    # Replenishment recommendation endpoints
│   │   │       └── forecast.py         # Demand forecasting endpoints
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py         # Authentication & registration logic
│   │       ├── category_service.py     # Category business logic & validation
│   │       ├── supplier_service.py     # Supplier business logic & validation
│   │       ├── product_service.py      # Product business logic, FK checks & validation
│   │       ├── inventory_service.py    # Atomic stock mutations & transaction ledger
│   │       ├── sales_service.py        # Sales transaction & stock-out processing
│   │       ├── purchase_order_service.py # PO lifecycle, transitions & receiving logic
│   │       ├── replenishment_service.py # Replenishment math, generation & lifecycle
│   │       └── forecast_service.py     # Deterministic SMA/WMA forecasting & continuous daily sales
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Shared in-memory test DB & fixtures
│   │   ├── test_auth.py                # Phase 2 test suite (9 tests)
│   │   ├── test_phase3.py              # Phase 3 comprehensive test suite (42 tests)
│   │   ├── test_phase4.py              # Phase 4 comprehensive test suite (31 tests)
│   │   ├── test_phase5.py              # Phase 5 comprehensive test suite (31 tests / 55 requirements)
│   │   ├── test_phase6.py              # Phase 6 comprehensive test suite (21 tests / 43 requirements)
│   │   └── test_phase7.py              # Phase 7 comprehensive test suite (29 tests / 56 requirements)
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
| **Sales Recording** (`POST /sales`) | Allowed | Allowed | Allowed |
| **Sales History Read** (`GET /sales/*`) | Allowed | Allowed | Read-Only |
| **Purchase Order Create** (`POST /purchase-orders`) | Allowed | Allowed | Forbidden (403) |
| **Purchase Order Update** (`PUT /purchase-orders/*`) | Allowed | Allowed | Forbidden (403) |
| **Purchase Order Status / Approve** (`PATCH .../status`) | Allowed | Allowed | Forbidden (403) |
| **Purchase Order Receiving** (`POST .../receive`) | Allowed | Allowed | Allowed |
| **Purchase Order Read** (`GET /purchase-orders/*`) | Allowed | Allowed | Read-Only |
| **Replenishment Generate** (`POST /replenishment/generate`) | Allowed | Allowed | Forbidden (403) |
| **Replenishment Query** (`GET /replenishment/recommendations*`) | Allowed | Allowed | Read-Only |
| **Replenishment Review** (`PATCH .../review`) | Allowed | Allowed | Forbidden (403) |
| **Replenishment Dismiss** (`PATCH .../dismiss`) | Allowed | Allowed | Forbidden (403) |
| **Forecast Generate** (`POST /forecast/generate*`) | Allowed | Allowed | Forbidden (403) |
| **Forecast Query & Detail** (`GET /forecast*`) | Allowed | Allowed | Read-Only |

---

## Phase 5: Sales & Purchase Order Management

### 1. Sales Module
- **Sales Recording (`POST /sales`):** Consumes available inventory by dispatching stock through `inventory_service.apply_stock_out`. Validates product status and ensures non-negative balances with row-level locking (`with_for_update`).
- **Immutable Ledger:** Every sale creates a permanent `Sale` record and stages an immutable `STOCK_OUT` transaction in the `inventory_transactions` ledger referencing the sale.
- **Strict Immutability:** Sales cannot be modified (`PUT`) or deleted (`DELETE`) via API.

### 2. Purchase Order Module & Lifecycle
Procurement orders coordinate supplier goods intake without directly altering inventory until physical goods arrive.

```
       [ DRAFT ] ──────────────┐
           │                   │
           ▼                   │
  [ PENDING_APPROVAL ] ────────┼──────> [ CANCELLED ]
           │                   │
           ▼                   │
      [ APPROVED ] ────────────┘
           │
           ▼
      [ ORDERED ]
           │
           ├────────────────────────┐
           ▼                        ▼
 [ PARTIALLY_RECEIVED ]  ───>  [ RECEIVED ]
```

- **Order Total Integrity:** Line item costs and purchase order totals are calculated exclusively on the server (`sum(quantity * unit_cost)`). Client total parameters are discarded.
- **Editable State:** Only orders in `DRAFT` status may be updated (`PUT /purchase-orders/{id}`).
- **Status Progression:** Validated state machine ensures orders proceed sequentially (`DRAFT` -> `PENDING_APPROVAL` -> `APPROVED` -> `ORDERED`). Orders can be cancelled from `DRAFT`, `PENDING_APPROVAL`, or `APPROVED`.
- **RBAC Enforcement:** Only `ADMIN` and `INVENTORY_MANAGER` can create, edit, approve, or cancel purchase orders. `WAREHOUSE_STAFF` cannot approve or transition commercial status.

### 3. Receiving Workflow
- **Goods Receipt (`POST /purchase-orders/{id}/receive`):** Allowed for `ADMIN`, `INVENTORY_MANAGER`, and `WAREHOUSE_STAFF` once an order is `ORDERED` or `PARTIALLY_RECEIVED`.
- **Partial Receiving:** Supports receiving batches of ordered quantities. Line items track `received_quantity` incrementally.
- **Automatic Inventory Updates:** Inbound items invoke `inventory_service.apply_stock_in`, incrementing `current_stock` and recording a `STOCK_IN` transaction linked to the purchase order number.
- **Status Evaluation:** If all items in an order are fulfilled (`received_quantity == quantity`), status transitions to `RECEIVED` and records `received_at`. Otherwise, status transitions to `PARTIALLY_RECEIVED`.
- **Over-Receiving Safeguards:** Receiving more than the remaining quantity (`quantity - received_quantity`) is strictly rejected.
- **Transactional Atomicity & Concurrency:** All receipts use row-level locks. If any item validation fails, the entire transaction rolls back without partial stock or receipt mutations.

---

## Phase 6: Smart Replenishment Engine

The Smart Replenishment Engine is a deterministic, rule-based recommendation system that evaluates active product inventory levels, sales velocity, supplier parameters, and safety thresholds to propose optimal stock replenishment.

### 1. Replenishment Calculation Formulas
- **Available Inventory Position:**
  $$\text{inventory\_position} = \max(0, \text{current\_stock} - \text{reserved\_stock})$$
- **Reorder Trigger:**
  Replenishment is triggered when:
  $$\text{inventory\_position} \le \text{reorder\_point}$$
  Products with $\text{inventory\_position} > \text{reorder\_point}$ do not trigger replenishment unless manually prioritized.
- **Average Daily Demand (30-day trailing window):**
  $$\text{average\_daily\_demand} = \frac{\sum \text{quantity of completed sales in last 30 days}}{30.0}$$
  Defaults to $0.0$ if no sales exist in the 30-day window.
- **Lead-Time Demand:**
  $$\text{lead\_time\_demand} = \text{average\_daily\_demand} \times \text{lead\_time\_days}$$
- **Base Target Requirement:**
  $$\text{base\_target} = \max(\text{target\_stock}, \text{lead\_time\_demand} + \text{safety\_stock})$$
- **Recommended Order Quantity & MOQ Adjustment:**
  $$\text{raw\_qty} = \max(0, \lceil \text{base\_target} - \text{inventory\_position} \rceil)$$
  If $\text{raw\_qty} > 0$ and $\text{raw\_qty} < \text{minimum\_order\_quantity}$, then $\text{recommended\_quantity} = \text{minimum\_order\_quantity}$, otherwise $\text{raw\_qty}$.
- **Priority Rules:**
  - `HIGH`: $\text{current\_stock} == 0$ OR $\text{inventory\_position} < \text{safety\_stock}$
  - `MEDIUM`: $\text{inventory\_position} \le \text{reorder\_point}$ (and not qualifying for HIGH)
  - `LOW`: $\text{inventory\_position} > \text{reorder\_point}$
- **Explainable Reasoning:**
  Generates explicit, human-readable rationale detailing stock position, threshold triggers, lead time demand, safety stock gap, and supplier MOQ constraints.

### 2. Recommendation Lifecycle & State Machine
```
   [ POST /generate ]
           │
           ▼
      [ PENDING ] ─────────────────────────┐
           │                               │
           ├────────────────┐              │
           ▼                ▼              ▼
     [ REVIEWED ]     [ DISMISSED ]   [ UPDATED IN-PLACE ]
                      (reason req.)  (on re-generate)
```
- **Lifecycle Statuses:** `PENDING` (initial), `REVIEWED` (evaluated by inventory team), `DISMISSED` (declined with required reason).
- **Deduplication:** Subsequent replenishment generation calls update existing `PENDING` recommendations in-place with latest metrics and recalculations, preventing duplicate pending queues.
- **Historical Preservation:** Recommendations in `REVIEWED` or `DISMISSED` state are immutable historical records and are preserved; subsequent runs create a fresh `PENDING` recommendation.
- **Strict Boundary:** The engine produces **recommendations only**. It **never** creates purchase orders automatically, approves orders, or mutates inventory stock balances.

---

## Phase 7: Demand Analysis & Forecasting

The Demand Analysis & Forecasting module provides deterministic, statistical time-series forecasting based on historical sales data. It aggregates historical sales into continuous daily demand sequences and projects future demand using classical moving average models.

> [!NOTE]
> **Deterministic Statistical Engine**:
> Phase 7 exclusively implements classical time-series techniques: Simple Moving Average (SMA) and Weighted Moving Average (WMA). It does **not** employ machine learning, neural networks, LSTM, transformers, or external AI/LLM APIs.

### 1. Daily Sales Aggregation
- **Continuous Calendar Timeline:** Sales quantities from the immutable `sales` ledger are aggregated per calendar date.
- **Zero-Sales Day Preservation:** Calendar days within the historical window with zero recorded sales are strictly maintained as `0.0` units. Days without sales are never omitted or compressed.

### 2. Forecasting Methodologies & Formulas

#### Simple Moving Average (SMA)
Calculates an unweighted arithmetic average of daily demand across the configured historical window:
$$\text{SMA} = \frac{\sum_{i=1}^{N} \text{daily\_demand}_i}{N}$$

- **Example (7-day window):**
  - Daily demand: $[10, 20, 15, 5, 10, 20, 20]$
  - Total demand: $100$
  - $\text{SMA} = 100 / 7 = 14.285714\dots$ units/day
  - Projected 3-day demand: $[14.2857, 14.2857, 14.2857]$ (Total: $42.8571$)

#### Weighted Moving Average (WMA)
Applies linear ascending weights to the most recent $W$ days in the historical window, giving higher prominence to recent sales activity:
$$\text{WMA} = \frac{\sum_{i=1}^{W} (\text{daily\_demand}_i \times i)}{\sum_{i=1}^{W} i} = \frac{\sum_{i=1}^{W} (\text{daily\_demand}_i \times i)}{\frac{W(W + 1)}{2}}$$

- **Default Weights (7-day WMA window):**
  - Oldest day (Day 1) $\to$ weight 1
  - Latest day (Day 7) $\to$ weight 7
  - Denominator $\sum_{i=1}^{7} i = 1 + 2 + 3 + 4 + 5 + 6 + 7 = 28$
- **Example (7-day window):**
  - Daily demand: $[10, 20, 15, 5, 10, 20, 20]$
  - Numerator: $(10\times 1) + (20\times 2) + (15\times 3) + (5\times 4) + (10\times 5) + (20\times 6) + (20\times 7) = 425$
  - $\text{WMA} = 425 / 28 = 15.178571\dots$ units/day

### 3. Forecast Horizon & Dating
- **Next-Day Sequencing:** Projections strictly begin on the **next calendar day** after the forecast generation date (e.g., generation on 2026-09-20 yields projections starting 2026-09-21).
- **Exact Daily Values:** Generates exactly `DEMAND_FORECAST_HORIZON_DAYS` future values stored with `Numeric(12, 4)` precision.
- **Model Versioning:** Initial deterministic implementation tagged with model version `"v1"`.

### 4. Forecast Lifecycle & Archiving
```
   [ POST /forecast/generate ]
                │
                ▼
      [ status = GENERATED ]
                │
                │ (when a new forecast is generated)
                ▼
      [ status = ARCHIVED ] (terminal, historical audit preserved)
```
- **Lifecycle Transition:** `GENERATED` $\to$ `ARCHIVED`. Generating a new forecast for a product automatically archives previous active forecasts.
- **Historical Preservation:** Archived forecasts are never deleted and remain fully retrievable for audit and comparative analysis.

### 5. Configuration Settings
Configurable via `.env` or environment variables:
- `DEMAND_FORECAST_HISTORY_DAYS`: Historical observation window in days (default: `30`, must be $> 0$).
- `DEMAND_FORECAST_HORIZON_DAYS`: Future forecast projection horizon in days (default: `7`, must be $> 0$).
- `DEMAND_FORECAST_WMA_WINDOW`: Window size for weighted moving average (default: `7`, must be $> 0$ and $\le$ history days).

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
Copy `.env.example` to `.env` and configure your database credentials:
```bash
cp .env.example .env
```

Apply all database migrations up to Phase 7:
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

### Sales Endpoints (Phase 5)
- `POST /sales` — Record sale (decrements stock, records immutable `STOCK_OUT` ledger entry, returns 201)
- `GET /sales` — Query sales history (`?product_id=`, `?sold_by=`, `?reference=`, `?start_date=`, `?end_date=`)
- `GET /sales/{sale_id}` — Retrieve specific sale details (strictly read-only; no `PUT`/`DELETE` endpoints)

### Purchase Order Endpoints (Phase 5)
- `POST /purchase-orders` — Create purchase order in `DRAFT` status (`ADMIN` / `INVENTORY_MANAGER`)
- `GET /purchase-orders` — List purchase orders (`?supplier_id=`, `?status=`, `?created_by=`, `?start_date=`, `?end_date=`)
- `GET /purchase-orders/{purchase_order_id}` — Retrieve purchase order with line items
- `PUT /purchase-orders/{purchase_order_id}` — Update purchase order (allowed only in `DRAFT` status)
- `PATCH /purchase-orders/{purchase_order_id}/status` — Advance status (`PENDING_APPROVAL`, `APPROVED`, `ORDERED`, or `CANCELLED`)
- `POST /purchase-orders/{purchase_order_id}/receive` — Process partial or full goods receipt (increments stock, records `STOCK_IN` ledger entry)

### Replenishment Endpoints (Phase 6)
- `POST /replenishment/generate` — Trigger replenishment evaluation for all active products (`ADMIN` / `INVENTORY_MANAGER`)
- `GET /replenishment/recommendations` — List recommendations (`?status=`, `?priority=`, `?product_id=`, `?supplier_id=`)
- `GET /replenishment/recommendations/{id}` — Retrieve recommendation detail by ID
- `PATCH /replenishment/recommendations/{id}/review` — Mark recommendation as `REVIEWED` (`ADMIN` / `INVENTORY_MANAGER`)
- `PATCH /replenishment/recommendations/{id}/dismiss` — Dismiss recommendation with mandatory reason (`ADMIN` / `INVENTORY_MANAGER`)

### Demand Forecasting Endpoints (Phase 7)
- `POST /forecast/generate` — Generate demand forecasts for all active products using SMA or WMA (`ADMIN` / `INVENTORY_MANAGER`)
- `POST /forecast/generate/{product_id}` — Generate forecast for a single product (`ADMIN` / `INVENTORY_MANAGER`)
- `GET /forecast` — List forecasts with filters (`?product_id=`, `?method=`, `?status=`, `?generated_from=`, `?generated_to=`)
- `GET /forecast/{forecast_id}` — Retrieve forecast detail with daily projection values
- `GET /forecast/products/{product_id}` — Retrieve latest forecast for a specific product

---

## Interactive Documentation & Swagger Testing

- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

Protected routes use Bearer token authentication. Click the green **Authorize** button in Swagger UI and input your access token to test endpoints directly.

---

## Running the Automated Test Suite

Run the full unified test suite across all completed phases (Phase 2 Auth, Phase 3 Catalog, Phase 4 Inventory, Phase 5 Sales & Purchase Orders, Phase 6 Replenishment Engine, and Phase 7 Demand Forecasting):

```bash
pytest -v
```

Or run Phase 7 tests individually:

```bash
pytest tests/test_phase7.py -v
```

---

## Frontend Setup & Execution (Phase 8)

The React SPA web frontend is located in `frontend/`:

```bash
cd frontend
npm install
npm run dev     # Starts Vite dev server at http://localhost:5173
npm test        # Runs Vitest unit & integration test suite
npm run build   # Builds production bundle to dist/
```
