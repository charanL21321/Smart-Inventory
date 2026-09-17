"""create demand forecasts and forecast values tables

Revision ID: 0006_create_demand_forecasts
Revises: 0005_create_replenishment_recommendations
Create Date: 2026-09-17 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_create_demand_forecasts'
down_revision: Union[str, None] = '0005_create_replenishment_recommendations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create demand_forecasts table
    op.create_table(
        'demand_forecasts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('forecast_method', sa.String(length=20), nullable=False),
        sa.Column('history_days', sa.Integer(), nullable=False),
        sa.Column('forecast_horizon_days', sa.Integer(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('model_version', sa.String(length=50), server_default='v1', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='GENERATED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('history_days > 0', name='chk_forecast_history_days_positive'),
        sa.CheckConstraint('forecast_horizon_days > 0', name='chk_forecast_horizon_positive'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_demand_forecasts_product_id', ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name='pk_demand_forecasts'),
    )
    op.create_index('ix_demand_forecasts_id', 'demand_forecasts', ['id'], unique=False)
    op.create_index('ix_demand_forecasts_product_id', 'demand_forecasts', ['product_id'], unique=False)
    op.create_index('ix_demand_forecasts_forecast_method', 'demand_forecasts', ['forecast_method'], unique=False)
    op.create_index('ix_demand_forecasts_status', 'demand_forecasts', ['status'], unique=False)
    op.create_index('ix_demand_forecasts_generated_at', 'demand_forecasts', ['generated_at'], unique=False)

    # 2. Create demand_forecast_values table
    op.create_table(
        'demand_forecast_values',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('forecast_id', sa.Integer(), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('forecast_quantity', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('forecast_quantity >= 0', name='chk_forecast_val_qty_non_negative'),
        sa.ForeignKeyConstraint(['forecast_id'], ['demand_forecasts.id'], name='fk_demand_forecast_values_forecast_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_demand_forecast_values'),
        sa.UniqueConstraint('forecast_id', 'forecast_date', name='uq_forecast_val_date'),
    )
    op.create_index('ix_demand_forecast_values_id', 'demand_forecast_values', ['id'], unique=False)
    op.create_index('ix_demand_forecast_values_forecast_id', 'demand_forecast_values', ['forecast_id'], unique=False)
    op.create_index('ix_demand_forecast_values_forecast_date', 'demand_forecast_values', ['forecast_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_demand_forecast_values_forecast_date', table_name='demand_forecast_values')
    op.drop_index('ix_demand_forecast_values_forecast_id', table_name='demand_forecast_values')
    op.drop_index('ix_demand_forecast_values_id', table_name='demand_forecast_values')
    op.drop_table('demand_forecast_values')

    op.drop_index('ix_demand_forecasts_generated_at', table_name='demand_forecasts')
    op.drop_index('ix_demand_forecasts_status', table_name='demand_forecasts')
    op.drop_index('ix_demand_forecasts_forecast_method', table_name='demand_forecasts')
    op.drop_index('ix_demand_forecasts_product_id', table_name='demand_forecasts')
    op.drop_index('ix_demand_forecasts_id', table_name='demand_forecasts')
    op.drop_table('demand_forecasts')
