"""Add position fields for factory contact information

Revision ID: 005_add_factory_contact_positions
Revises: 004_add_contract_cycle_fields
Create Date: 2025-11-30

This migration adds position (cargo/役職) fields for:
- Supervisor (指揮命令者)
- Client complaint contact (派遣先苦情処理担当者)
- Client responsible person (派遣先責任者)

This allows each factory to have full organizational structure configuration.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_factory_contact_positions'
down_revision = '004_add_contract_cycle_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add position fields to factories table."""
    # Add position field for supervisor (if not already present)
    try:
        op.add_column('factories', sa.Column(
            'supervisor_position',
            sa.String(100),
            nullable=True,
            comment='Supervisor position (e.g., 課長, 部長, リーダー)'
        ))
    except Exception:
        pass  # Column already exists

    # Add position field for client complaint contact
    op.add_column('factories', sa.Column(
        'client_complaint_position',
        sa.String(100),
        nullable=True,
        comment='Client complaint contact position (e.g., 担当者, 課長, 部長)'
    ))

    # Add position field for client responsible person
    op.add_column('factories', sa.Column(
        'client_responsible_position',
        sa.String(100),
        nullable=True,
        comment='Client responsible person position (e.g., 課長, 部長, 責任者)'
    ))


def downgrade() -> None:
    """Remove position fields from factories table."""
    try:
        op.drop_column('factories', 'supervisor_position')
    except Exception:
        pass

    try:
        op.drop_column('factories', 'client_complaint_position')
    except Exception:
        pass

    try:
        op.drop_column('factories', 'client_responsible_position')
    except Exception:
        pass
