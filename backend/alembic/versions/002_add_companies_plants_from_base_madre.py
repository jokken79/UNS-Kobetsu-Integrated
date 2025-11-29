"""add companies and plants tables from base madre schema

Revision ID: 002_add_companies_plants
Revises: 001_add_kobetsu_keiyakusho
Create Date: 2024-11-29

This migration adds companies and plants tables matching the Base Madre schema.
This allows Kobetsu to sync and use the same data structure as Base Madre.

Tables added:
- companies (派遣先企業) - Client companies from Base Madre
- plants (工場/事業所) - Plant locations from Base Madre
- jigyosho (事業所) - Regional offices from Base Madre

The existing 'factories' table remains for backward compatibility but new
features should use companies/plants for consistency with Base Madre.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_companies_plants'
down_revision = '001_add_kobetsu_keiyakusho'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # COMPANIES TABLE (from Base Madre)
    # ========================================
    op.create_table(
        'companies',
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('name_kana', sa.String(255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('fax', sa.String(50), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('responsible_department', sa.String(100), nullable=True),
        sa.Column('responsible_name', sa.String(100), nullable=True),
        sa.Column('responsible_phone', sa.String(50), nullable=True),
        sa.Column('contract_start', sa.Date(), nullable=True),
        sa.Column('contract_end', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        # Add Base Madre tracking
        sa.Column('base_madre_company_id', sa.Integer(), nullable=True, comment='Reference to Base Madre company_id'),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True, comment='Last sync from Base Madre'),

        sa.PrimaryKeyConstraint('company_id'),
        sa.UniqueConstraint('base_madre_company_id', name='uq_base_madre_company_id'),
    )
    op.create_index('ix_companies_name', 'companies', ['name'])
    op.create_index('ix_companies_is_active', 'companies', ['is_active'])
    op.create_index('ix_companies_base_madre_id', 'companies', ['base_madre_company_id'])

    # ========================================
    # JIGYOSHO TABLE (Regional Offices)
    # ========================================
    op.create_table(
        'jigyosho',
        sa.Column('jigyosho_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('jigyosho_name', sa.String(255), nullable=False),
        sa.Column('jigyosho_code', sa.String(50), nullable=True),
        sa.Column('jigyosho_address', sa.Text(), nullable=True),
        sa.Column('jigyosho_phone', sa.String(50), nullable=True),
        sa.Column('jigyosho_fax', sa.String(50), nullable=True),
        sa.Column('manager_name', sa.String(100), nullable=True),
        sa.Column('manager_phone', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        # Base Madre tracking
        sa.Column('base_madre_jigyosho_id', sa.Integer(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('jigyosho_id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('base_madre_jigyosho_id', name='uq_base_madre_jigyosho_id'),
    )
    op.create_index('ix_jigyosho_company_id', 'jigyosho', ['company_id'])
    op.create_index('ix_jigyosho_base_madre_id', 'jigyosho', ['base_madre_jigyosho_id'])

    # ========================================
    # PLANTS TABLE (from Base Madre)
    # ========================================
    op.create_table(
        'plants',
        sa.Column('plant_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('jigyosho_id', sa.Integer(), nullable=True),
        sa.Column('plant_name', sa.String(255), nullable=False),
        sa.Column('plant_code', sa.String(50), nullable=True),
        sa.Column('plant_address', sa.Text(), nullable=True),
        sa.Column('plant_phone', sa.String(50), nullable=True),
        sa.Column('manager_name', sa.String(100), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),

        # Base Madre tracking
        sa.Column('base_madre_plant_id', sa.Integer(), nullable=True, comment='Reference to Base Madre plant_id'),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True, comment='Last sync from Base Madre'),

        sa.PrimaryKeyConstraint('plant_id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['jigyosho_id'], ['jigyosho.jigyosho_id'], ondelete='SET NULL'),
        sa.UniqueConstraint('base_madre_plant_id', name='uq_base_madre_plant_id'),
    )
    op.create_index('ix_plants_company_id', 'plants', ['company_id'])
    op.create_index('ix_plants_jigyosho_id', 'plants', ['jigyosho_id'])
    op.create_index('ix_plants_plant_name', 'plants', ['plant_name'])
    op.create_index('ix_plants_is_active', 'plants', ['is_active'])
    op.create_index('ix_plants_base_madre_id', 'plants', ['base_madre_plant_id'])

    # ========================================
    # Update kobetsu_keiyakusho to reference new tables
    # ========================================
    # Add new columns for company/plant references (optional foreign keys)
    # Keep factory_id for backward compatibility
    op.add_column('kobetsu_keiyakusho',
        sa.Column('company_id', sa.Integer(), nullable=True, comment='Reference to companies table'))
    op.add_column('kobetsu_keiyakusho',
        sa.Column('plant_id', sa.Integer(), nullable=True, comment='Reference to plants table'))

    # Add foreign key constraints
    op.create_foreign_key(
        'fk_kobetsu_company', 'kobetsu_keiyakusho', 'companies',
        ['company_id'], ['company_id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_kobetsu_plant', 'kobetsu_keiyakusho', 'plants',
        ['plant_id'], ['plant_id'], ondelete='SET NULL'
    )

    op.create_index('ix_kobetsu_company_id', 'kobetsu_keiyakusho', ['company_id'])
    op.create_index('ix_kobetsu_plant_id', 'kobetsu_keiyakusho', ['plant_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_kobetsu_plant_id', 'kobetsu_keiyakusho')
    op.drop_index('ix_kobetsu_company_id', 'kobetsu_keiyakusho')

    # Drop foreign keys
    op.drop_constraint('fk_kobetsu_plant', 'kobetsu_keiyakusho', type_='foreignkey')
    op.drop_constraint('fk_kobetsu_company', 'kobetsu_keiyakusho', type_='foreignkey')

    # Drop columns
    op.drop_column('kobetsu_keiyakusho', 'plant_id')
    op.drop_column('kobetsu_keiyakusho', 'company_id')

    # Drop tables in reverse order (due to foreign keys)
    op.drop_table('plants')
    op.drop_table('jigyosho')
    op.drop_table('companies')
