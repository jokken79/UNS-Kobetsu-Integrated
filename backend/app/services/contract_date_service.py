"""
Contract Date Service
Handles contract date calculations based on factory cycle configurations.
"""
from datetime import date, datetime, timedelta
from calendar import monthrange
from typing import Tuple, Optional

from sqlalchemy.orm import Session
from app.models.factory import Factory, ContractCycleType, ContractCycleDayType


class ContractDateService:
    """Service for calculating contract dates based on factory cycles."""

    def __init__(self, db: Session):
        self.db = db

    def calculate_contract_dates(
        self,
        factory_id: int,
        employee_start_date: Optional[date] = None,
    ) -> Tuple[date, date]:
        """
        Calculate dispatch start and end dates based on factory cycle.

        Args:
            factory_id: Factory ID
            employee_start_date: Employee's start date (defaults to today)

        Returns:
            Tuple of (dispatch_start_date, dispatch_end_date)

        Raises:
            ValueError: If factory not found

        Examples:
            Misuzu (monthly, month-end):
            - Input: start 3/25 → Output: (3/25, 4/30)
            - Input: start 1/31 → Output: (1/31, 2/28 or 2/29)

            Takao (annual, 9/30):
            - Input: start 3/25 → Output: (3/25, 9/30)
            - Input: start 10/15 → Output: (10/15, 9/30 next year)
        """
        factory = self.db.query(Factory).filter(Factory.id == factory_id).first()
        if not factory:
            raise ValueError(f"Factory {factory_id} not found")

        start_date = employee_start_date or date.today()

        if factory.contract_cycle_type == ContractCycleType.MONTHLY:
            return self._calculate_monthly_cycle(
                start_date,
                factory.fiscal_year_end_day,
                factory.cycle_day_type
            )
        else:  # ANNUAL
            return self._calculate_annual_cycle(
                start_date,
                factory.fiscal_year_end_month,
                factory.fiscal_year_end_day,
                factory.cycle_day_type
            )

    def _calculate_monthly_cycle(
        self,
        start_date: date,
        fiscal_end_day: int,
        day_type: ContractCycleDayType
    ) -> Tuple[date, date]:
        """
        Calculate monthly cycle dates.

        Monthly cycles go from start date to the end of the next month.
        Example: March 25 → April 30 (next month's end)
        """
        # Get next month
        if start_date.month == 12:
            next_month_year = start_date.year + 1
            next_month = 1
        else:
            next_month_year = start_date.year
            next_month = start_date.month + 1

        if day_type == ContractCycleDayType.MONTH_END:
            # Always last day of next month
            last_day = monthrange(next_month_year, next_month)[1]
            end_date = date(next_month_year, next_month, last_day)
        else:  # FIXED
            # Use fixed day, but clamp to valid range for month
            last_day = monthrange(next_month_year, next_month)[1]
            clamped_day = min(fiscal_end_day, last_day)
            end_date = date(next_month_year, next_month, clamped_day)

        return (start_date, end_date)

    def _calculate_annual_cycle(
        self,
        start_date: date,
        fiscal_end_month: int,
        fiscal_end_day: int,
        day_type: ContractCycleDayType
    ) -> Tuple[date, date]:
        """
        Calculate annual cycle dates.

        Annual contracts end at the fiscal year end date.
        Fiscal year can be any month (e.g., 3/31 or 9/30 in Japan).

        Example (fiscal end 9/30):
        - Start 3/25/2025 → End 9/30/2025 (same year)
        - Start 10/15/2025 → End 9/30/2026 (next year)
        """
        # Determine which fiscal year this start date falls into
        fiscal_end_this_year = date(start_date.year, fiscal_end_month, 1)

        # Get valid last day of fiscal end month (handle Feb 29, etc.)
        last_day = monthrange(start_date.year, fiscal_end_month)[1]
        clamped_day = min(fiscal_end_day, last_day) if day_type == ContractCycleDayType.FIXED else last_day
        fiscal_end_this_year = date(start_date.year, fiscal_end_month, clamped_day)

        # If start date is after fiscal end this year, contract ends next year
        if start_date > fiscal_end_this_year:
            end_year = start_date.year + 1
        else:
            end_year = start_date.year

        # Create end date with proper day clamping for leap years
        end_day = monthrange(end_year, fiscal_end_month)[1]
        end_date_day = min(fiscal_end_day, end_day) if day_type == ContractCycleDayType.FIXED else end_day
        end_date = date(end_year, fiscal_end_month, end_date_day)

        return (start_date, end_date)

    def calculate_renewal_dates(
        self,
        current_contract_id: int
    ) -> Tuple[date, date]:
        """
        Calculate dates for next contract based on current contract.

        The new contract starts the day after current contract ends,
        and its duration follows the same factory cycle rules.

        Args:
            current_contract_id: ID of current contract to renew

        Returns:
            Tuple of (new_start_date, new_end_date)
        """
        from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho

        current_contract = self.db.query(KobetsuKeiyakusho).filter(
            KobetsuKeiyakusho.id == current_contract_id
        ).first()

        if not current_contract:
            raise ValueError(f"Contract {current_contract_id} not found")

        # New contract starts day after current ends
        new_start_date = current_contract.dispatch_end_date + timedelta(days=1)

        # Calculate the new end date based on factory cycle
        _, new_end_date = self.calculate_contract_dates(
            factory_id=current_contract.factory_id,
            employee_start_date=new_start_date
        )

        return (new_start_date, new_end_date)

    def get_cycle_description(self, factory_id: int) -> str:
        """
        Get human-readable description of factory's contract cycle.

        Returns:
            String like "月次契約 (毎月更新)" or "年間契約 (10/1-9/30)"
        """
        factory = self.db.query(Factory).filter(Factory.id == factory_id).first()
        if not factory:
            return ""

        if factory.contract_cycle_type == ContractCycleType.MONTHLY:
            return "月次契約 (毎月更新)"
        else:
            # Calculate fiscal year start (day after fiscal end of prev year)
            start_month = factory.fiscal_year_end_month + 1
            start_day = 1
            if start_month > 12:
                start_month = 1

            end_month = factory.fiscal_year_end_month
            end_day = factory.fiscal_year_end_day

            return f"年間契約 ({start_month}/{start_day}-{end_month}/{end_day})"

    def is_leap_year(self, year: int) -> bool:
        """Check if a year is a leap year."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
