export type UserRole = 'ADMIN' | 'INVENTORY_MANAGER' | 'WAREHOUSE_STAFF';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface Category {
  id: number;
  name: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CategoryCreate {
  name: string;
  description?: string;
}

export interface CategoryUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface Supplier {
  id: number;
  name: string;
  contact_person?: string | null;
  email: string;
  phone: string;
  address?: string | null;
  lead_time_days: number;
  minimum_order_quantity: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface SupplierCreate {
  name: string;
  contact_person?: string;
  email: string;
  phone: string;
  address?: string;
  lead_time_days?: number;
  minimum_order_quantity?: number;
}

export interface SupplierUpdate {
  name?: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  lead_time_days?: number;
  minimum_order_quantity?: number;
  is_active?: boolean;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  description?: string | null;
  category_id: number;
  supplier_id: number;
  price: number;
  reorder_point: number;
  safety_stock: number;
  target_stock: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  category?: Category;
  supplier?: Supplier;
}

export interface ProductCreate {
  name: string;
  sku: string;
  description?: string;
  category_id: number;
  supplier_id: number;
  price: number;
  reorder_point: number;
  safety_stock: number;
  target_stock: number;
}

export interface ProductUpdate {
  name?: string;
  sku?: string;
  description?: string;
  category_id?: number;
  supplier_id?: number;
  price?: number;
  reorder_point?: number;
  safety_stock?: number;
  target_stock?: number;
  is_active?: boolean;
}

export type InventoryStatus = 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK';

export interface Inventory {
  id: number;
  product_id: number;
  current_stock: number;
  reserved_stock: number;
  available_stock: number;
  status: InventoryStatus;
  last_restocked_at?: string | null;
  created_at: string;
  updated_at?: string;
  product?: Product;
}

export type TransactionType = 'STOCK_IN' | 'STOCK_OUT' | 'ADJUSTMENT_IN' | 'ADJUSTMENT_OUT';

export interface InventoryTransaction {
  id: number;
  product_id: number;
  transaction_type: TransactionType;
  quantity: number;
  previous_stock: number;
  resulting_stock: number;
  reason?: string | null;
  reference?: string | null;
  performed_by: number;
  created_at: string;
  product?: Product;
  user?: User;
}

export interface StockInRequest {
  product_id: number;
  quantity: number;
  reason?: string;
  reference?: string;
}

export interface StockOutRequest {
  product_id: number;
  quantity: number;
  reason?: string;
  reference?: string;
}

export type AdjustmentType = 'IN' | 'OUT';

export interface StockAdjustmentRequest {
  product_id: number;
  adjustment_type: AdjustmentType;
  quantity: number;
  reason: string;
}

export interface Sale {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  total_amount: number;
  sold_by: number;
  reference?: string | null;
  created_at: string;
  product?: Product;
  user?: User;
}

export interface SaleCreate {
  product_id: number;
  quantity: number;
  unit_price?: number;
  reference?: string;
}

export type PurchaseOrderStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'ORDERED'
  | 'PARTIALLY_RECEIVED'
  | 'RECEIVED'
  | 'CANCELLED';

export interface PurchaseOrderItem {
  id: number;
  purchase_order_id: number;
  product_id: number;
  quantity: number;
  unit_cost: number;
  total_cost: number;
  received_quantity: number;
  created_at: string;
  updated_at?: string;
  product?: Product;
}

export interface PurchaseOrderItemCreate {
  product_id: number;
  quantity: number;
  unit_cost: number;
}

export interface PurchaseOrder {
  id: number;
  order_number: string;
  supplier_id: number;
  status: PurchaseOrderStatus;
  total_amount: number;
  notes?: string | null;
  created_by: number;
  approved_by?: number | null;
  ordered_at?: string | null;
  expected_delivery_date?: string | null;
  received_at?: string | null;
  created_at: string;
  updated_at?: string;
  items: PurchaseOrderItem[];
  supplier?: Supplier;
}

export interface PurchaseOrderCreate {
  supplier_id: number;
  notes?: string;
  expected_delivery_date?: string;
  items: PurchaseOrderItemCreate[];
}

export interface PurchaseOrderUpdate {
  notes?: string;
  expected_delivery_date?: string;
  items?: PurchaseOrderItemCreate[];
}

export interface PurchaseOrderStatusUpdate {
  status: PurchaseOrderStatus;
}

export interface PurchaseOrderReceiveItem {
  product_id: number;
  received_quantity: number;
}

export interface PurchaseOrderReceiveRequest {
  items: PurchaseOrderReceiveItem[];
}

export type RecommendationPriority = 'LOW' | 'MEDIUM' | 'HIGH';
export type RecommendationStatus = 'PENDING' | 'REVIEWED' | 'DISMISSED';

export interface ReplenishmentRecommendation {
  id: number;
  product_id: number;
  supplier_id: number;
  current_stock: number;
  reserved_stock: number;
  inventory_position: number;
  reorder_point: number;
  safety_stock: number;
  target_stock: number;
  average_daily_demand: number;
  lead_time_days: number;
  lead_time_demand: number;
  recommended_quantity: number;
  minimum_order_quantity: number;
  priority: RecommendationPriority;
  reason: string;
  dismissal_reason?: string | null;
  status: RecommendationStatus;
  generated_at: string;
  updated_at: string;
  product?: Product;
  supplier?: Supplier;
}

export interface ReplenishmentDismissRequest {
  reason: string;
}

export type ForecastMethod = 'SMA' | 'WMA';
export type ForecastStatus = 'GENERATED' | 'ARCHIVED';

export interface DemandForecastValue {
  id: number;
  forecast_id: number;
  forecast_date: string;
  forecast_quantity: number;
  created_at: string;
}

export interface DemandForecast {
  id: number;
  product_id: number;
  product_name?: string | null;
  forecast_method: ForecastMethod;
  history_days: number;
  forecast_horizon_days: number;
  model_version: string;
  status: ForecastStatus;
  generated_at: string;
  total_forecast_quantity: number;
  average_daily_forecast: number;
  explanation?: string | null;
  created_at: string;
  updated_at: string;
  values?: DemandForecastValue[];
}

export type NotificationType =
  | 'LOW_STOCK'
  | 'OUT_OF_STOCK'
  | 'REPLENISHMENT_RECOMMENDATION'
  | 'PURCHASE_ORDER_STATUS'
  | 'PURCHASE_ORDER_RECEIVED'
  | 'FORECAST_GENERATED';

export type NotificationPriority = 'LOW' | 'MEDIUM' | 'HIGH';

export interface Notification {
  id: number;
  user_id?: number;
  notification_type: NotificationType;
  priority: NotificationPriority;
  title: string;
  message: string;
  product_id?: number | null;
  supplier_id?: number | null;
  purchase_order_id?: number | null;
  replenishment_recommendation_id?: number | null;
  forecast_id?: number | null;
  is_read: boolean;
  created_at: string;
  read_at?: string | null;
}

export interface UnreadCountResponse {
  unread_count: number;
}
