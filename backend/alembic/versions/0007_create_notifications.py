"""create notifications table

Revision ID: 0007_create_notifications
Revises: 0006_create_demand_forecasts
Create Date: 2026-09-17 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_create_notifications'
down_revision: Union[str, None] = '0006_create_demand_forecasts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), nullable=True),
        sa.Column('purchase_order_id', sa.Integer(), nullable=True),
        sa.Column('replenishment_recommendation_id', sa.Integer(), nullable=True),
        sa.Column('forecast_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_notifications_user_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_notifications_product_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], name='fk_notifications_supplier_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], name='fk_notifications_purchase_order_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['replenishment_recommendation_id'], ['replenishment_recommendations.id'], name='fk_notifications_rep_rec_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['forecast_id'], ['demand_forecasts.id'], name='fk_notifications_forecast_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_notifications'),
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'], unique=False)
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('ix_notifications_notification_type', 'notifications', ['notification_type'], unique=False)
    op.create_index('ix_notifications_priority', 'notifications', ['priority'], unique=False)
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'], unique=False)
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'], unique=False)
    op.create_index('ix_notifications_product_id', 'notifications', ['product_id'], unique=False)
    op.create_index('ix_notifications_user_read_created', 'notifications', ['user_id', 'is_read', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_notifications_user_read_created', table_name='notifications')
    op.drop_index('ix_notifications_product_id', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_priority', table_name='notifications')
    op.drop_index('ix_notifications_notification_type', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_notifications_id', table_name='notifications')
    op.drop_table('notifications')
