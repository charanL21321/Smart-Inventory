# Smart Inventory & Stock Replenishment Platform — Frontend

An enterprise-grade React single-page web application built with **React 18**, **TypeScript**, **Vite**, and **Lucide React** icons. It provides real-time stock control, purchase order workflows, rule-based automated replenishment recommendations, and time-series demand forecasting (SMA & WMA).

---

## Architecture Overview

```
frontend/
├── src/
│   ├── api/                  # Centralized typed HTTP client with JWT interceptor
│   │   ├── client.ts         # Base fetch wrapper, error normalizer, 401 handler
│   │   ├── auth.ts           # Login & session inspection
│   │   ├── categories.ts     # Category CRUD
│   │   ├── suppliers.ts      # Supplier directory & lead time/MOQ
│   │   ├── products.ts       # Product catalog & stock parameters
│   │   ├── inventory.ts      # Real-time balances & stock movements
│   │   ├── sales.ts          # Sales order recording & history
│   │   ├── purchaseOrders.ts # PO lifecycle & goods receipt
│   │   ├── replenishment.ts  # Rule-based replenishment engine
│   │   ├── forecast.ts       # SMA/WMA forecasting models
│   │   └── index.ts
│   ├── components/
│   │   ├── common/           # Button, Input, Select, Modal, Badge, StatusBadge,
│   │   │                     # Spinner, ErrorAlert, EmptyState, ConfirmDialog, ForecastChart
│   │   └── layout/           # AppLayout, Header, Sidebar
│   ├── context/
│   │   └── AuthContext.tsx   # JWT session management & role helpers
│   ├── pages/                # 14 complete web views
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Products.tsx
│   │   ├── Categories.tsx
│   │   ├── Suppliers.tsx
│   │   ├── Inventory.tsx
│   │   ├── InventoryTransactions.tsx
│   │   ├── Sales.tsx
│   │   ├── PurchaseOrders.tsx
│   │   ├── PurchaseOrderDetail.tsx
│   │   ├── Replenishment.tsx
│   │   ├── Forecasts.tsx
│   │   ├── ForecastDetail.tsx
│   │   └── Profile.tsx
│   ├── routes/
│   │   ├── AppRoutes.tsx     # Application router tree & 404 handler
│   │   └── ProtectedRoute.tsx# Role-based route guard & 403 screen
│   ├── test/                 # Vitest & React Testing Library suites
│   ├── types/
│   │   └── index.ts          # Strict TypeScript types matching FastAPI schemas
│   ├── App.tsx
│   ├── index.css             # Enterprise CSS design tokens & layout styles
│   └── main.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env
```

---

## Getting Started

### Prerequisites
- Node.js >= 18 (e.g. Node LTS v20.18.0)
- FastAPI backend running at `http://localhost:8000`

### Environment Configuration
Copy `.env.example` to `.env`:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Installation
```bash
npm install
```

### Development Server
Run Vite hot-reloading dev server on port `5173`:
```bash
npm run dev
```

### Running Tests
Execute unit and component tests via Vitest:
```bash
npm test
```

### Production Build
Type-check and produce optimized static assets in `dist/`:
```bash
npm run build
```

---

## Role-Based Access Control (RBAC)

The frontend mirrors backend authorization rules:

| Feature / Page | ADMIN | INVENTORY_MANAGER | WAREHOUSE_STAFF |
|---|:---:|:---:|:---:|
| **Dashboard** | Full Access | Full Access | Full Access |
| **Catalog (Products, Categories, Suppliers)** | Create/Edit/Delete | Create/Edit/Delete | Read Only |
| **Stock In / Stock Out** | Allowed | Allowed | Allowed |
| **Stock Adjustment** | Allowed | Allowed | **Forbidden (403)** |
| **Sales Recording** | Allowed | Allowed | Allowed |
| **PO Create / Approve / Order** | Allowed | Allowed | **Read Only** |
| **PO Goods Receiving** | Allowed | Allowed | Allowed |
| **Run Replenishment Engine** | Allowed | Allowed | **Read Only** |
| **Review / Dismiss Recommendation** | Allowed | Allowed | **Read Only** |
| **Run Demand Forecast Models** | Allowed | Allowed | **Read Only** |
