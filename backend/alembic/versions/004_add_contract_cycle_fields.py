"""Add contract cycle fields for factory-specific renewal configuration

Revision ID: 004_add_contract_cycle_fields
Revises: 003_add_performance_indexes
Create Date: 2025-11-30

This migration adds:
1. Contract cycle configuration to factories table
2. Previous contract tracking to kobetsu_keiyakusho table
3. Data migration for known factory configurations
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '004_add_contract_cycle_fields'
down_revision = '003_add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # 1. ADD CONTRACT CYCLE FIELDS TO FACTORIES
    # ========================================

    # Create ENUMs for contract cycle types
    contract_cycle_type_enum = postgresql.ENUM(
        'monthly', 'annual',
        name='contract_cycle_type',
        create_type=True
    )
    contract_cycle_type_enum.create(op.get_bind())

    cycle_day_type_enum = postgresql.ENUM(
        'fixed', 'month_end',
        name='contract_cycle_day_type',
        create_type=True
    )
    cycle_day_type_enum.create(op.get_bind())

    # Add contract cycle columns to factories table
    op.add_column('factories',
        sa.Column('contract_cycle_type',
                  contract_cycle_type_enum,
                  nullable=False,
                  server_default='annual',
                  comment='月次契約 or 年間契約')
    )

    op.add_column('factories',
        sa.Column('cycle_day_type',
                  cycle_day_type_enum,
                  nullable=False,
                  server_default='fixed',
                  comment='固定日 or 月末')
    )

    op.add_column('factories',
        sa.Column('fiscal_year_end_month',
                  sa.Integer(),
                  nullable=False,
                  server_default='3',
                  comment='決算月 (1-12)')
    )

    op.add_column('factories',
        sa.Column('fiscal_year_end_day',
                  sa.Integer(),
                  nullable=False,
                  server_default='31',
                  comment='決算日 (1-31)')
    )

    op.add_column('factories',
        sa.Column('contract_renewal_days_before',
                  sa.Integer(),
                  nullable=False,
                  server_default='30',
                  comment='自動更新通知日数')
    )

    # Add check constraints for fiscal dates
    op.create_check_constraint(
        'ck_fiscal_month',
        'factories',
        'fiscal_year_end_month BETWEEN 1 AND 12'
    )

    op.create_check_constraint(
        'ck_fiscal_day',
        'factories',
        'fiscal_year_end_day BETWEEN 1 AND 31'
    )

    op.create_check_constraint(
        'ck_renewal_days',
        'factories',
        'contract_renewal_days_before BETWEEN 0 AND 365'
    )

    # ========================================
    # 2. ADD PREVIOUS CONTRACT TRACKING
    # ========================================

    op.add_column('kobetsu_keiyakusho',
        sa.Column('previous_contract_id',
                  sa.Integer(),
                  nullable=True,
                  comment='ID of the previous contract (for renewals)')
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_kobetsu_previous_contract',
        'kobetsu_keiyakusho',
        'kobetsu_keiyakusho',
        ['previous_contract_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add index for efficient renewal chain queries
    op.create_index(
        'ix_kobetsu_previous_contract',
        'kobetsu_keiyakusho',
        ['previous_contract_id'],
        postgresql_using='btree'
    )

    # ========================================
    # 3. DATA MIGRATION FOR KNOWN FACTORIES
    # ========================================

    # Update Misuzu factories (monthly cycle, month-end, September fiscal year)
    op.execute("""
        UPDATE factories
        SET contract_cycle_type = 'monthly',
            cycle_day_type = 'month_end',
            fiscal_year_end_month = 9,
            fiscal_year_end_day = 30,
            contract_renewal_days_before = 30
        WHERE company_name ILIKE '%ミスズ%'
           OR company_name ILIKE '%misuzu%'
           OR company_name ILIKE '%美鈴%'
    """)

    # Update Takao factories (annual cycle, fixed date, September 30)
    op.execute("""
        UPDATE factories
        SET contract_cycle_type = 'annual',
            cycle_day_type = 'fixed',
            fiscal_year_end_month = 9,
            fiscal_year_end_day = 30,
            contract_renewal_days_before = 30
        WHERE company_name ILIKE '%タカオ%'
           OR company_name ILIKE '%takao%'
           OR company_name ILIKE '%高雄%'
    """)

    # Update other known factories based on common patterns
    # Default remains annual/fixed/March 31 for unknown factories


def downgrade():
    # ========================================
    # REMOVE CONTRACT TRACKING FROM KOBETSU
    # ========================================

    # Drop index first
    op.drop_index('ix_kobetsu_previous_contract', 'kobetsu_keiyakusho')

    # Drop foreign key constraint
    op.drop_constraint('fk_kobetsu_previous_contract', 'kobetsu_keiyakusho', type_='foreignkey')

    # Drop column
    op.drop_column('kobetsu_keiyakusho', 'previous_contract_id')

    # ========================================
    # REMOVE CONTRACT CYCLE FIELDS FROM FACTORIES
    # ========================================

    # Drop check constraints
    op.drop_constraint('ck_renewal_days', 'factories', type_='check')
    op.drop_constraint('ck_fiscal_day', 'factories', type_='check')
    op.drop_constraint('ck_fiscal_month', 'factories', type_='check')

    # Drop columns
    op.drop_column('factories', 'contract_renewal_days_before')
    op.drop_column('factories', 'fiscal_year_end_day')
    op.drop_column('factories', 'fiscal_year_end_month')
    op.drop_column('factories', 'cycle_day_type')
    op.drop_column('factories', 'contract_cycle_type')

    # Drop ENUMs
    contract_cycle_type_enum = postgresql.ENUM(
        'monthly', 'annual',
        name='contract_cycle_type'
    )
    contract_cycle_type_enum.drop(op.get_bind())

    cycle_day_type_enum = postgresql.ENUM(
        'fixed', 'month_end',
        name='contract_cycle_day_type'
    )
    cycle_day_type_enum.drop(op.get_bind())