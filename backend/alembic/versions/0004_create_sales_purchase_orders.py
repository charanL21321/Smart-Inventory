"""create sales and purchase orders tables

Revision ID: 0004_create_sales_purchase_orders
Revises: 0003_create_inventory_tables
Create Date: 2026-09-17 10:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_create_sales_purchase_orders'
down_revision: Union[str, None] = '0003_create_inventory_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create sales table
    op.create_table(
        'sales',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('sold_by', sa.Integer(), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('quantity > 0', name='chk_sales_quantity_positive'),
        sa.CheckConstraint('unit_price >= 0', name='chk_sales_unit_price_non_negative'),
        sa.CheckConstraint('total_amount >= 0', name='chk_sales_total_amount_non_negative'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_sales_product_id_products', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['sold_by'], ['users.id'], name='fk_sales_sold_by_users', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_sales'),
    )
    op.create_index('ix_sales_id', 'sales', ['id'], unique=False)
    op.create_index('ix_sales_product_id', 'sales', ['product_id'], unique=False)
    op.create_index('ix_sales_sold_by', 'sales', ['sold_by'], unique=False)
    op.create_index('ix_sales_created_at', 'sales', ['created_at'], unique=False)

    # 2. Create purchase_orders table
    op.create_table(
        'purchase_orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('total_amount', sa.Float(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('ordered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expected_delivery_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('total_amount >= 0', name='chk_purchase_orders_total_amount_non_negative'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_purchase_orders_supplier_id_suppliers', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], name='fk_purchase_orders_created_by_users', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name='fk_purchase_orders_approved_by_users', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_purchase_orders'),
        sa.UniqueConstraint('order_number', name='uq_purchase_orders_order_number'),
    )
    op.create_index('ix_purchase_orders_id', 'purchase_orders', ['id'], unique=False)
    op.create_index('ix_purchase_orders_order_number', 'purchase_orders', ['order_number'], unique=True)
    op.create_index('ix_purchase_orders_supplier_id', 'purchase_orders', ['supplier_id'], unique=False)
    op.create_index('ix_purchase_orders_status', 'purchase_orders', ['status'], unique=False)
    op.create_index('ix_purchase_orders_created_by', 'purchase_orders', ['created_by'], unique=False)
    op.create_index('ix_purchase_orders_created_at', 'purchase_orders', ['created_at'], unique=False)

    # 3. Create purchase_order_items table
    op.create_table(
        'purchase_order_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('received_quantity', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('unit_cost', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('quantity > 0', name='chk_po_items_quantity_positive'),
        sa.CheckConstraint('received_quantity >= 0', name='chk_po_items_received_quantity_non_negative'),
        sa.CheckConstraint('received_quantity <= quantity', name='chk_po_items_received_lte_quantity'),
        sa.CheckConstraint('unit_cost >= 0', name='chk_po_items_unit_cost_non_negative'),
        sa.CheckConstraint('total_cost >= 0', name='chk_po_items_total_cost_non_negative'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], name='fk_purchase_order_items_po_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_purchase_order_items_product_id', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_purchase_order_items'),
    )
    op.create_index('ix_purchase_order_items_id', 'purchase_order_items', ['id'], unique=False)
    op.create_index('ix_purchase_order_items_purchase_order_id', 'purchase_order_items', ['purchase_order_id'], unique=False)
    op.create_index('ix_purchase_order_items_product_id', 'purchase_order_items', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_purchase_order_items_product_id', table_name='purchase_order_items')
    op.drop_index('ix_purchase_order_items_purchase_order_id', table_name='purchase_order_items')
    op.drop_index('ix_purchase_order_items_id', table_name='purchase_order_items')
    op.drop_table('purchase_order_items')

    op.drop_index('ix_purchase_orders_created_at', table_name='purchase_orders')
    op.drop_index('ix_purchase_orders_created_by', table_name='purchase_orders')
    op.drop_index('ix_purchase_orders_status', table_name='purchase_orders')
    op.drop_index('ix_purchase_orders_supplier_id', table_name='purchase_orders')
    op.drop_index('ix_purchase_orders_order_number', table_name='purchase_orders')
    op.drop_index('ix_purchase_orders_id', table_name='purchase_orders')
    op.drop_table('purchase_orders')

    op.drop_index('ix_sales_created_at', table_name='sales')
    op.drop_index('ix_sales_sold_by', table_name='sales')
    op.drop_index('ix_sales_product_id', table_name='sales')
    op.drop_index('ix_sales_id', table_name='sales')
    op.drop_table('sales')
