"""
Performance-optimized service for Kobetsu queries.
Uses indexes created in migration 003_add_performance_indexes.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, func, text
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql import exists

from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho
from app.models.employee import Employee
from app.models.factory import Factory
from app.models.kobetsu_employee import KobetsuEmployee


class PerformanceOptimizedService:
    """Service with optimized queries leveraging performance indexes."""

    def __init__(self, db: Session):
        self.db = db

    def get_expiring_contracts(
        self,
        days_ahead: int = 30,
        status: str = 'active',
        limit: Optional[int] = None
    ) -> List[KobetsuKeiyakusho]:
        """
        Get contracts expiring within specified days.
        Uses index: ix_kobetsu_status_dates (status, dispatch_start_date, dispatch_end_date)
        """
        expiry_date = date.today() + timedelta(days=days_ahead)

        query = self.db.query(KobetsuKeiyakusho)\
            .options(
                joinedload(KobetsuKeiyakusho.factory),
                selectinload(KobetsuKeiyakusho.employees)
            )\
            .filter(and_(
                KobetsuKeiyakusho.status == status,
                KobetsuKeiyakusho.dispatch_end_date <= expiry_date,
                KobetsuKeiyakusho.dispatch_end_date >= date.today()
            ))\
            .order_by(KobetsuKeiyakusho.dispatch_end_date)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_factory_contracts(
        self,
        factory_id: int,
        status: Optional[str] = None,
        include_employees: bool = False
    ) -> List[KobetsuKeiyakusho]:
        """
        Get all contracts for a specific factory.
        Uses index: ix_kobetsu_factory_status (factory_id, status)
        """
        filters = [KobetsuKeiyakusho.factory_id == factory_id]
        if status:
            filters.append(KobetsuKeiyakusho.status == status)

        query = self.db.query(KobetsuKeiyakusho)\
            .filter(and_(*filters))

        if include_employees:
            query = query.options(selectinload(KobetsuKeiyakusho.employees))

        return query.all()

    def get_company_plant_contracts(
        self,
        company_id: int,
        plant_id: Optional[int] = None,
        status: str = 'active'
    ) -> List[KobetsuKeiyakusho]:
        """
        Get contracts for Base Madre company/plant.
        Uses index: ix_kobetsu_company_plant_status (company_id, plant_id, status)
        """
        filters = [
            KobetsuKeiyakusho.company_id == company_id,
            KobetsuKeiyakusho.status == status
        ]

        if plant_id:
            filters.append(KobetsuKeiyakusho.plant_id == plant_id)

        return self.db.query(KobetsuKeiyakusho)\
            .filter(and_(*filters))\
            .all()

    def get_recent_contracts(
        self,
        days_back: int = 7,
        limit: int = 10
    ) -> List[KobetsuKeiyakusho]:
        """
        Get recently created contracts.
        Uses index: ix_kobetsu_created_at (created_at)
        """
        cutoff_date = datetime.now() - timedelta(days=days_back)

        return self.db.query(KobetsuKeiyakusho)\
            .filter(KobetsuKeiyakusho.created_at >= cutoff_date)\
            .order_by(KobetsuKeiyakusho.created_at.desc())\
            .limit(limit)\
            .all()

    def get_employees_with_expiring_visas(
        self,
        days_ahead: int = 90,
        limit: Optional[int] = None
    ) -> List[Employee]:
        """
        Get active employees with expiring visas.
        Uses partial index: ix_employees_status_visa (status, visa_expiry_date) WHERE status = 'active'
        """
        warning_date = date.today() + timedelta(days=days_ahead)

        query = self.db.query(Employee)\
            .filter(and_(
                Employee.status == 'active',  # Matches partial index condition
                Employee.visa_expiry_date <= warning_date,
                Employee.visa_expiry_date >= date.today()
            ))\
            .order_by(Employee.visa_expiry_date)

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_contract_employees_in_period(
        self,
        contract_id: int,
        start_date: date,
        end_date: date
    ) -> List[KobetsuEmployee]:
        """
        Get employees assigned to a contract within a date range.
        Uses index: ix_kobetsu_employees_dates
        """
        return self.db.query(KobetsuEmployee)\
            .options(joinedload(KobetsuEmployee.employee))\
            .filter(and_(
                KobetsuEmployee.kobetsu_keiyakusho_id == contract_id,
                or_(
                    KobetsuEmployee.individual_start_date.is_(None),
                    KobetsuEmployee.individual_start_date <= end_date
                ),
                or_(
                    KobetsuEmployee.individual_end_date.is_(None),
                    KobetsuEmployee.individual_end_date >= start_date
                )
            ))\
            .all()

    def get_active_contracts_summary_from_view(self) -> List[Dict[str, Any]]:
        """
        Query the materialized view for active contracts summary.
        Uses: mv_active_contracts_summary
        """
        result = self.db.execute(text("""
            SELECT
                id,
                contract_number,
                dispatch_start_date,
                dispatch_end_date,
                factory_company_name,
                factory_plant_name,
                company_name,
                plant_name,
                employee_count,
                CASE
                    WHEN dispatch_end_date < CURRENT_DATE THEN 'expired'
                    WHEN dispatch_end_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'expiring_soon'
                    ELSE 'active'
                END as urgency_status
            FROM mv_active_contracts_summary
            ORDER BY dispatch_end_date
        """))

        return [dict(row._mapping) for row in result]

    def refresh_active_contracts_view(self) -> bool:
        """
        Refresh the materialized view for active contracts.
        Should be called periodically (e.g., via scheduled job).
        """
        try:
            self.db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_active_contracts_summary"))
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def get_contract_statistics(self) -> Dict[str, Any]:
        """
        Get optimized contract statistics using appropriate indexes.
        """
        # Using aggregate functions with filtered conditions
        stats = self.db.query(
            func.count(KobetsuKeiyakusho.id).label('total_contracts'),
            func.count(KobetsuKeiyakusho.id).filter(
                KobetsuKeiyakusho.status == 'active'
            ).label('active_contracts'),
            func.count(KobetsuKeiyakusho.id).filter(and_(
                KobetsuKeiyakusho.status == 'active',
                KobetsuKeiyakusho.dispatch_end_date <= date.today() + timedelta(days=30)
            )).label('expiring_soon'),
            func.count(KobetsuKeiyakusho.id).filter(
                KobetsuKeiyakusho.created_at >= datetime.now() - timedelta(days=7)
            ).label('created_this_week')
        ).first()

        return {
            'total_contracts': stats.total_contracts or 0,
            'active_contracts': stats.active_contracts or 0,
            'expiring_soon': stats.expiring_soon or 0,
            'created_this_week': stats.created_this_week or 0,
            'timestamp': datetime.now().isoformat()
        }

    def batch_update_contract_status(self, contract_ids: List[int], new_status: str) -> int:
        """
        Efficiently update multiple contracts' status.
        """
        if not contract_ids:
            return 0

        # Use bulk update for better performance
        result = self.db.query(KobetsuKeiyakusho)\
            .filter(KobetsuKeiyakusho.id.in_(contract_ids))\
            .update(
                {KobetsuKeiyakusho.status: new_status},
                synchronize_session=False
            )

        self.db.commit()
        return result

    def search_contracts_optimized(
        self,
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        factory_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Optimized search with pagination.
        Uses multiple indexes based on filter conditions.
        """
        query = self.db.query(KobetsuKeiyakusho)

        # Build filters based on available indexes
        filters = []

        # Use ix_kobetsu_factory_status if both factory and status provided
        if factory_id and status:
            filters.extend([
                KobetsuKeiyakusho.factory_id == factory_id,
                KobetsuKeiyakusho.status == status
            ])
        elif factory_id:
            filters.append(KobetsuKeiyakusho.factory_id == factory_id)
        elif status:
            filters.append(KobetsuKeiyakusho.status == status)

        # Date range filter (uses ix_kobetsu_dispatch_dates)
        if date_from:
            filters.append(KobetsuKeiyakusho.dispatch_end_date >= date_from)
        if date_to:
            filters.append(KobetsuKeiyakusho.dispatch_start_date <= date_to)

        # Text search (consider adding full-text search index for better performance)
        if search_term:
            filters.append(
                or_(
                    KobetsuKeiyakusho.contract_number.ilike(f'%{search_term}%'),
                    KobetsuKeiyakusho.worksite_name.ilike(f'%{search_term}%')
                )
            )

        if filters:
            query = query.filter(and_(*filters))

        # Get total count
        total = query.count()

        # Apply pagination
        contracts = query\
            .order_by(KobetsuKeiyakusho.created_at.desc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()

        return {
            'contracts': contracts,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }

    def analyze_query_performance(self, query_string: str) -> List[str]:
        """
        Analyze query performance using EXPLAIN ANALYZE.
        Useful for debugging and optimization.
        """
        result = self.db.execute(text(f"EXPLAIN ANALYZE {query_string}"))
        return [row[0] for row in result]