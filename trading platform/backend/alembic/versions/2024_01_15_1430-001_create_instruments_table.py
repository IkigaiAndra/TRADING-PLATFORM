"""create instruments table

Revision ID: 001
Revises: 
Create Date: 2024-01-15 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create instruments table with JSONB metadata and indexes"""
    
    # Create instruments table
    op.create_table(
        'instruments',
        sa.Column('instrument_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('instrument_type', sa.String(length=20), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('instrument_id')
    )
    
    # Create unique index on symbol and instrument_type combination
    op.create_index(
        'uq_instruments_symbol_type',
        'instruments',
        ['symbol', 'instrument_type'],
        unique=True
    )
    
    # Create index on symbol for fast lookups
    op.create_index(
        'idx_instruments_symbol',
        'instruments',
        ['symbol'],
        unique=False
    )
    
    # Create index on instrument_type for filtering by type
    op.create_index(
        'idx_instruments_type',
        'instruments',
        ['instrument_type'],
        unique=False
    )


def downgrade() -> None:
    """Drop instruments table and all indexes"""
    
    # Drop indexes first
    op.drop_index('idx_instruments_type', table_name='instruments')
    op.drop_index('idx_instruments_symbol', table_name='instruments')
    op.drop_index('uq_instruments_symbol_type', table_name='instruments')
    
    # Drop table
    op.drop_table('instruments')
