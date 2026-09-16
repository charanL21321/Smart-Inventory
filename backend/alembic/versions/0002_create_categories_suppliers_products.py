"""create categories suppliers products

Revision ID: 0002_create_categories_suppliers_products
Revises: 0001_create_users_table
Create Date: 2026-09-16 15:17:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_create_categories_suppliers_products'
down_revision: Union[str, None] = '0001_create_users_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id', name='pk_categories'),
    )
    op.create_index('ix_categories_id', 'categories', ['id'], unique=False)
    op.create_index('ix_categories_name', 'categories', ['name'], unique=True)

    # 2. Create suppliers table
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('contact_person', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('minimum_order_quantity', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id', name='pk_suppliers'),
    )
    op.create_index('ix_suppliers_id', 'suppliers', ['id'], unique=False)
    op.create_index('ix_suppliers_name', 'suppliers', ['name'], unique=False)

    # 3. Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('reorder_point', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('safety_stock', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('target_stock', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name='fk_products_category_id_categories', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_products_supplier_id_suppliers', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_products'),
    )
    op.create_index('ix_products_id', 'products', ['id'], unique=False)
    op.create_index('ix_products_name', 'products', ['name'], unique=False)
    op.create_index('ix_products_sku', 'products', ['sku'], unique=True)
    op.create_index('ix_products_category_id', 'products', ['category_id'], unique=False)
    op.create_index('ix_products_supplier_id', 'products', ['supplier_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_products_supplier_id', table_name='products')
    op.drop_index('ix_products_category_id', table_name='products')
    op.drop_index('ix_products_sku', table_name='products')
    op.drop_index('ix_products_name', table_name='products')
    op.drop_index('ix_products_id', table_name='products')
    op.drop_table('products')

    op.drop_index('ix_suppliers_name', table_name='suppliers')
    op.drop_index('ix_suppliers_id', table_name='suppliers')
    op.drop_table('suppliers')

    op.drop_index('ix_categories_name', table_name='categories')
    op.drop_index('ix_categories_id', table_name='categories')
    op.drop_table('categories')
