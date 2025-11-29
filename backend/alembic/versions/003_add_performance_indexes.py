"""Add performance indexes and constraints for optimization

Revision ID: 003_add_performance_indexes
Revises: 002_add_companies_plants
Create Date: 2024-11-29

This migration adds performance indexes for common queries and ensures data integrity
with additional constraints.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_performance_indexes'
down_revision = '002_add_companies_plants'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # PERFORMANCE INDEXES
    # ========================================

    # Composite index for status-based date range queries (most common filter pattern)
    # This replaces simple status index with a more efficient compound index
    op.create_index(
        'ix_kobetsu_status_dates',
        'kobetsu_keiyakusho',
        ['status', 'dispatch_start_date', 'dispatch_end_date'],
        postgresql_using='btree'
    )

    # Composite index for factory+status queries (common filter combination)
    op.create_index(
        'ix_kobetsu_factory_status',
        'kobetsu_keiyakusho',
        ['factory_id', 'status'],
        postgresql_using='btree'
    )

    # Composite index for company+plant+status queries (new Base Madre integration)
    op.create_index(
        'ix_kobetsu_company_plant_status',
        'kobetsu_keiyakusho',
        ['company_id', 'plant_id', 'status'],
        postgresql_using='btree'
    )

    # Index for searching by created_at (for recent contracts dashboard)
    op.create_index(
        'ix_kobetsu_created_at',
        'kobetsu_keiyakusho',
        ['created_at'],
        postgresql_using='btree'
    )

    # Composite index for employee assignment queries
    op.create_index(
        'ix_kobetsu_employees_dates',
        'kobetsu_employees',
        ['kobetsu_keiyakusho_id', 'individual_start_date', 'individual_end_date'],
        postgresql_using='btree'
    )

    # Index for active employees with visa expiry (compliance monitoring)
    # Note: ix_employees_status already exists, so we create a composite for visa monitoring
    op.create_index(
        'ix_employees_status_visa',
        'employees',
        ['status', 'visa_expiry_date'],
        postgresql_using='btree',
        postgresql_where=sa.text("status = 'active'")  # Partial index for active only
    )

    # Index for factory lines lookups
    op.create_index(
        'ix_factory_lines_active',
        'factory_lines',
        ['factory_id', 'is_active'],
        postgresql_using='btree',
        postgresql_where=sa.text("is_active = true")  # Partial index
    )

    # ========================================
    # UNIQUE CONSTRAINTS
    # ========================================

    # Make contract_number truly unique (currently has non-unique index)
    # First drop the existing non-unique index
    op.drop_index('ix_kobetsu_contract_number', 'kobetsu_keiyakusho')

    # Then create a unique constraint which automatically creates a unique index
    op.create_unique_constraint(
        'uq_kobetsu_contract_number',
        'kobetsu_keiyakusho',
        ['contract_number']
    )

    # ========================================
    # CHECK CONSTRAINTS
    # ========================================

    # Ensure company/plant consistency:
    # If plant_id is set, company_id must also be set (plant belongs to company)
    op.create_check_constraint(
        'ck_kobetsu_company_plant_consistency',
        'kobetsu_keiyakusho',
        sa.text("(plant_id IS NULL) OR (company_id IS NOT NULL)"),
        info={'description': 'If plant_id is set, company_id must also be set'}
    )

    # Ensure valid date ranges for individual employee assignments
    op.create_check_constraint(
        'ck_kobetsu_employees_dates',
        'kobetsu_employees',
        sa.text("(individual_start_date IS NULL) OR (individual_end_date IS NULL) OR (individual_start_date <= individual_end_date)"),
        info={'description': 'Individual assignment dates must be valid'}
    )

    # Ensure positive rates for kobetsu_employees
    op.create_check_constraint(
        'ck_kobetsu_employees_rates',
        'kobetsu_employees',
        sa.text("""
            (hourly_rate IS NULL OR hourly_rate >= 0) AND
            (overtime_rate IS NULL OR overtime_rate >= 0) AND
            (night_shift_rate IS NULL OR night_shift_rate >= 0) AND
            (holiday_rate IS NULL OR holiday_rate >= 0) AND
            (billing_rate IS NULL OR billing_rate >= 0)
        """),
        info={'description': 'All rates must be non-negative'}
    )

    # ========================================
    # PERFORMANCE VIEWS (Optional - for complex queries)
    # ========================================

    # Create a materialized view for active contracts summary (refresh periodically)
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_active_contracts_summary AS
        SELECT
            k.id,
            k.contract_number,
            k.status,
            k.dispatch_start_date,
            k.dispatch_end_date,
            k.factory_id,
            k.company_id,
            k.plant_id,
            f.company_name as factory_company_name,
            f.plant_name as factory_plant_name,
            c.name as company_name,
            p.plant_name,
            COUNT(DISTINCT ke.employee_id) as employee_count,
            k.created_at,
            k.updated_at
        FROM kobetsu_keiyakusho k
        LEFT JOIN factories f ON k.factory_id = f.id
        LEFT JOIN companies c ON k.company_id = c.company_id
        LEFT JOIN plants p ON k.plant_id = p.plant_id
        LEFT JOIN kobetsu_employees ke ON k.id = ke.kobetsu_keiyakusho_id
        WHERE k.status = 'active'
        GROUP BY
            k.id, k.contract_number, k.status, k.dispatch_start_date, k.dispatch_end_date,
            k.factory_id, k.company_id, k.plant_id,
            f.company_name, f.plant_name, c.name, p.plant_name,
            k.created_at, k.updated_at
    """)

    # Create index on materialized view
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_active_contracts_id
        ON mv_active_contracts_summary (id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mv_active_contracts_dates
        ON mv_active_contracts_summary (dispatch_end_date)
    """)


def downgrade():
    # Drop materialized view and its indexes
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_active_contracts_summary CASCADE")

    # Drop check constraints
    op.drop_constraint('ck_kobetsu_employees_rates', 'kobetsu_employees', type_='check')
    op.drop_constraint('ck_kobetsu_employees_dates', 'kobetsu_employees', type_='check')
    op.drop_constraint('ck_kobetsu_company_plant_consistency', 'kobetsu_keiyakusho', type_='check')

    # Drop unique constraint and recreate non-unique index
    op.drop_constraint('uq_kobetsu_contract_number', 'kobetsu_keiyakusho', type_='unique')
    op.create_index('ix_kobetsu_contract_number', 'kobetsu_keiyakusho', ['contract_number'])

    # Drop performance indexes in reverse order
    op.drop_index('ix_factory_lines_active', 'factory_lines')
    op.drop_index('ix_employees_status_visa', 'employees')
    op.drop_index('ix_kobetsu_employees_dates', 'kobetsu_employees')
    op.drop_index('ix_kobetsu_created_at', 'kobetsu_keiyakusho')
    op.drop_index('ix_kobetsu_company_plant_status', 'kobetsu_keiyakusho')
    op.drop_index('ix_kobetsu_factory_status', 'kobetsu_keiyakusho')
    op.drop_index('ix_kobetsu_status_dates', 'kobetsu_keiyakusho')