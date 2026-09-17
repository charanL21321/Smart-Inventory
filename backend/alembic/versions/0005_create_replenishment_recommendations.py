"""create replenishment recommendations table

Revision ID: 0005_create_replenishment_recommendations
Revises: 0004_create_sales_purchase_orders
Create Date: 2026-09-17 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_create_replenishment_recommendations'
down_revision: Union[str, None] = '0004_create_sales_purchase_orders'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'replenishment_recommendations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('current_stock', sa.Integer(), nullable=False),
        sa.Column('reserved_stock', sa.Integer(), nullable=False),
        sa.Column('inventory_position', sa.Integer(), nullable=False),
        sa.Column('reorder_point', sa.Integer(), nullable=False),
        sa.Column('safety_stock', sa.Integer(), nullable=False),
        sa.Column('target_stock', sa.Integer(), nullable=False),
        sa.Column('average_daily_demand', sa.Float(), nullable=False),
        sa.Column('lead_time_days', sa.Integer(), nullable=False),
        sa.Column('lead_time_demand', sa.Float(), nullable=False),
        sa.Column('recommended_quantity', sa.Integer(), nullable=False),
        sa.Column('minimum_order_quantity', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('dismissal_reason', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('current_stock >= 0', name='chk_rec_current_stock_non_negative'),
        sa.CheckConstraint('reserved_stock >= 0', name='chk_rec_reserved_stock_non_negative'),
        sa.CheckConstraint('inventory_position >= 0', name='chk_rec_inv_pos_non_negative'),
        sa.CheckConstraint('reorder_point >= 0', name='chk_rec_reorder_point_non_negative'),
        sa.CheckConstraint('safety_stock >= 0', name='chk_rec_safety_stock_non_negative'),
        sa.CheckConstraint('target_stock > 0', name='chk_rec_target_stock_positive'),
        sa.CheckConstraint('average_daily_demand >= 0', name='chk_rec_avg_daily_demand_non_negative'),
        sa.CheckConstraint('lead_time_days >= 0', name='chk_rec_lead_time_days_non_negative'),
        sa.CheckConstraint('lead_time_demand >= 0', name='chk_rec_lead_time_demand_non_negative'),
        sa.CheckConstraint('recommended_quantity >= 0', name='chk_rec_recommended_qty_non_negative'),
        sa.CheckConstraint('minimum_order_quantity > 0', name='chk_rec_moq_positive'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_replenishment_recommendations_product_id', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_replenishment_recommendations_supplier_id', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_replenishment_recommendations'),
    )
    op.create_index('ix_replenishment_recommendations_id', 'replenishment_recommendations', ['id'], unique=False)
    op.create_index('ix_replenishment_recommendations_product_id', 'replenishment_recommendations', ['product_id'], unique=False)
    op.create_index('ix_replenishment_recommendations_supplier_id', 'replenishment_recommendations', ['supplier_id'], unique=False)
    op.create_index('ix_replenishment_recommendations_status', 'replenishment_recommendations', ['status'], unique=False)
    op.create_index('ix_replenishment_recommendations_priority', 'replenishment_recommendations', ['priority'], unique=False)
    op.create_index('ix_replenishment_recommendations_generated_at', 'replenishment_recommendations', ['generated_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_replenishment_recommendations_generated_at', table_name='replenishment_recommendations')
    op.drop_index('ix_replenishment_recommendations_priority', table_name='replenishment_recommendations')
    op.drop_index('ix_replenishment_recommendations_status', table_name='replenishment_recommendations')
    op.drop_index('ix_replenishment_recommendations_supplier_id', table_name='replenishment_recommendations')
    op.drop_index('ix_replenishment_recommendations_product_id', table_name='replenishment_recommendations')
    op.drop_index('ix_replenishment_recommendations_id', table_name='replenishment_recommendations')
    op.drop_table('replenishment_recommendations')
