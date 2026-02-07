"""create indicators and patterns tables

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create indicators and patterns tables"""
    
    # Create indicators table
    op.create_table(
        'indicators',
        sa.Column('instrument_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('indicator_name', sa.String(length=50), nullable=False),
        sa.Column('value', sa.NUMERIC(precision=20, scale=6), nullable=False),
        sa.Column('metadata', JSONB, nullable=True),
        sa.ForeignKeyConstraint(
            ['instrument_id'], 
            ['instruments.instrument_id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('instrument_id', 'timestamp', 'timeframe', 'indicator_name')
    )
    
    # Create composite index on (instrument_id, timeframe, indicator_name, timestamp)
    # This index is optimized for queries filtering by instrument, timeframe, and indicator
    # and ordering by timestamp (most recent first)
    op.create_index(
        'idx_indicators_lookup',
        'indicators',
        ['instrument_id', 'timeframe', 'indicator_name', 'timestamp'],
        unique=False
    )
    
    # Convert indicators table to TimescaleDB hypertable
    # Partition by timestamp with default chunk interval (7 days)
    op.execute("""
        SELECT create_hypertable(
            'indicators',
            'timestamp',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE
        );
    """)
    
    # Create patterns table
    op.create_table(
        'patterns',
        sa.Column('pattern_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('pattern_type', sa.String(length=50), nullable=False),
        sa.Column('start_timestamp', sa.TIMESTAMP(), nullable=False),
        sa.Column('end_timestamp', sa.TIMESTAMP(), nullable=True),
        sa.Column('confidence', sa.NUMERIC(precision=5, scale=2), nullable=False),
        sa.Column('metadata', JSONB, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(
            ['instrument_id'], 
            ['instruments.instrument_id'],
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('pattern_id')
    )
    
    # Create index on (instrument_id, timeframe, start_timestamp)
    # This index is optimized for queries filtering by instrument and timeframe
    # and ordering by start_timestamp (most recent first)
    op.create_index(
        'idx_patterns_instrument',
        'patterns',
        ['instrument_id', 'timeframe', 'start_timestamp'],
        unique=False
    )
    
    # Create index on (pattern_type, start_timestamp)
    # This index is optimized for queries filtering by pattern type
    # and ordering by start_timestamp (most recent first)
    op.create_index(
        'idx_patterns_type',
        'patterns',
        ['pattern_type', 'start_timestamp'],
        unique=False
    )
    
    # Add check constraint for confidence range [0.00, 100.00]
    op.create_check_constraint(
        'ck_patterns_confidence_range',
        'patterns',
        'confidence >= 0.00 AND confidence <= 100.00'
    )
    
    # Add check constraint for timestamp ordering
    # If end_timestamp is not NULL, it must be >= start_timestamp
    op.create_check_constraint(
        'ck_patterns_timestamp_order',
        'patterns',
        'end_timestamp IS NULL OR end_timestamp >= start_timestamp'
    )


def downgrade() -> None:
    """Drop indicators and patterns tables and all constraints"""
    
    # Drop patterns table constraints
    op.drop_constraint('ck_patterns_timestamp_order', 'patterns', type_='check')
    op.drop_constraint('ck_patterns_confidence_range', 'patterns', type_='check')
    
    # Drop patterns table indexes
    op.drop_index('idx_patterns_type', table_name='patterns')
    op.drop_index('idx_patterns_instrument', table_name='patterns')
    
    # Drop patterns table
    op.drop_table('patterns')
    
    # Drop indicators table index
    op.drop_index('idx_indicators_lookup', table_name='indicators')
    
    # Drop indicators table (TimescaleDB will automatically handle hypertable cleanup)
    op.drop_table('indicators')
