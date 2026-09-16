"""create inventory tables

Revision ID: 0003_create_inventory_tables
Revises: 0002_create_categories_suppliers_products
Create Date: 2026-09-16 16:11:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_create_inventory_tables'
down_revision: Union[str, None] = '0002_create_categories_suppliers_products'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create inventory table
    op.create_table(
        'inventory',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('current_stock', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('reserved_stock', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_inventory_product_id_products', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_inventory'),
        sa.UniqueConstraint('product_id', name='uq_inventory_product_id'),
    )
    op.create_index('ix_inventory_id', 'inventory', ['id'], unique=False)
    op.create_index('ix_inventory_product_id', 'inventory', ['product_id'], unique=True)
    op.create_index('ix_inventory_current_stock', 'inventory', ['current_stock'], unique=False)

    # 2. Create inventory_transactions table
    op.create_table(
        'inventory_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=30), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('previous_stock', sa.Integer(), nullable=False),
        sa.Column('resulting_stock', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], name='fk_inventory_transactions_performed_by_users', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_inventory_transactions_product_id_products', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_inventory_transactions'),
    )
    op.create_index('ix_inventory_transactions_id', 'inventory_transactions', ['id'], unique=False)
    op.create_index('ix_inventory_transactions_product_id', 'inventory_transactions', ['product_id'], unique=False)
    op.create_index('ix_inventory_transactions_transaction_type', 'inventory_transactions', ['transaction_type'], unique=False)
    op.create_index('ix_inventory_transactions_performed_by', 'inventory_transactions', ['performed_by'], unique=False)
    op.create_index('ix_inventory_transactions_created_at', 'inventory_transactions', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_inventory_transactions_created_at', table_name='inventory_transactions')
    op.drop_index('ix_inventory_transactions_performed_by', table_name='inventory_transactions')
    op.drop_index('ix_inventory_transactions_transaction_type', table_name='inventory_transactions')
    op.drop_index('ix_inventory_transactions_product_id', table_name='inventory_transactions')
    op.drop_index('ix_inventory_transactions_id', table_name='inventory_transactions')
    op.drop_table('inventory_transactions')

    op.drop_index('ix_inventory_current_stock', table_name='inventory')
    op.drop_index('ix_inventory_product_id', table_name='inventory')
    op.drop_index('ix_inventory_id', table_name='inventory')
    op.drop_table('inventory')
