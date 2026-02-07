"""create prices hypertable

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create prices table and convert to TimescaleDB hypertable"""
    
    # Create prices table
    op.create_table(
        'prices',
        sa.Column('instrument_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('open', sa.NUMERIC(precision=20, scale=6), nullable=False),
        sa.Column('high', sa.NUMERIC(precision=20, scale=6), nullable=False),
        sa.Column('low', sa.NUMERIC(precision=20, scale=6), nullable=False),
        sa.Column('close', sa.NUMERIC(precision=20, scale=6), nullable=False),
        sa.Column('volume', sa.BIGINT(), nullable=False),
        sa.ForeignKeyConstraint(
            ['instrument_id'], 
            ['instruments.instrument_id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('instrument_id', 'timestamp', 'timeframe')
    )
    
    # Create composite index on (instrument_id, timeframe, timestamp)
    # This index is optimized for queries filtering by instrument and timeframe
    # and ordering by timestamp (most recent first)
    op.create_index(
        'idx_prices_instrument_timeframe',
        'prices',
        ['instrument_id', 'timeframe', 'timestamp'],
        unique=False
    )
    
    # Convert to TimescaleDB hypertable
    # Partition by timestamp with default chunk interval (7 days)
    op.execute("""
        SELECT create_hypertable(
            'prices',
            'timestamp',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE
        );
    """)
    
    # Add check constraint for OHLC relationships
    # Ensures Low <= Open <= High AND Low <= Close <= High
    op.create_check_constraint(
        'ck_prices_ohlc_relationships',
        'prices',
        'low <= open AND open <= high AND low <= close AND close <= high AND low <= high'
    )
    
    # Add check constraint for non-negative volume
    op.create_check_constraint(
        'ck_prices_volume_non_negative',
        'prices',
        'volume >= 0'
    )


def downgrade() -> None:
    """Drop prices table and all constraints"""
    
    # Drop check constraints
    op.drop_constraint('ck_prices_volume_non_negative', 'prices', type_='check')
    op.drop_constraint('ck_prices_ohlc_relationships', 'prices', type_='check')
    
    # Drop index
    op.drop_index('idx_prices_instrument_timeframe', table_name='prices')
    
    # Drop table (TimescaleDB will automatically handle hypertable cleanup)
    op.drop_table('prices')
