"""
Employee Compatibility Service
Validates that multiple employees can work under the same contract.
"""
from dataclasses import dataclass
from datetime import time, date
from typing import List, Dict, Any, Optional
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.employee import Employee


@dataclass
class EmployeeCompatibilityIssue:
    """Represents a compatibility issue for an employee."""
    employee_id: int
    employee_number: str
    employee_name: str
    line_name: str
    issue_type: str  # 'different_line', 'different_rate', 'incompatible_schedule', 'inactive_employee'
    reason: str
    severity: str   # 'error' (must be separate) or 'warning'


class EmployeeCompatibilityValidator:
    """
    Validates that multiple employees can work under the same contract.

    Compatible employees must have:
    ✅ Same factory_line_id (trabajando en la MISMA línea)
    ✅ Same hourly_rate (mismo tanka for this contract)
    ✅ Same work schedule (same start_time, end_time, days, breaks)
    ✅ Same contract period (dispatch_start_date, dispatch_end_date)

    Note: The contract DEFINES the schedule, rates, and period.
    This validator ensures employees are compatible with those terms.
    """

    def __init__(self, db: Session):
        self.db = db

    def validate_employees(
        self,
        employee_ids: List[int],
        factory_line_id: Optional[int] = None,
        hourly_rate: Optional[Decimal] = None,
        work_start_time: Optional[time] = None,
        work_end_time: Optional[time] = None,
        work_days: Optional[List[str]] = None,
        break_time_minutes: Optional[int] = None,
        dispatch_start_date: Optional[date] = None,
        dispatch_end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Validate that all selected employees are compatible for a single contract.

        Args:
            employee_ids: List of employee IDs to validate
            factory_line_id: Expected factory line ID (optional)
            hourly_rate: Contract hourly rate (optional)
            work_start_time: Contract work start time (optional)
            work_end_time: Contract work end time (optional)
            work_days: Contract work days (optional)
            break_time_minutes: Contract break time (optional)
            dispatch_start_date: Contract start date (optional)
            dispatch_end_date: Contract end date (optional)

        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "compatible_count": int,
                "incompatible_count": int,
                "compatible": [employee dicts],
                "incompatible": [employee dicts with issues],
                "suggestions": [suggestion strings],
                "summary": summary string
            }
        """
        # Fetch all employees
        employees = self.db.query(Employee).filter(Employee.id.in_(employee_ids)).all()

        if not employees:
            raise ValueError("No employees found")

        if len(employees) != len(employee_ids):
            found_ids = {e.id for e in employees}
            missing_ids = set(employee_ids) - found_ids
            raise ValueError(f"Employees not found: {missing_ids}")

        compatible = []
        incompatible = []

        # Determine the expected line if not provided
        # Use the most common line among employees
        if factory_line_id is None and employees:
            line_counts = {}
            for emp in employees:
                if emp.factory_line_id:
                    line_counts[emp.factory_line_id] = line_counts.get(emp.factory_line_id, 0) + 1

            if line_counts:
                factory_line_id = max(line_counts.items(), key=lambda x: x[1])[0]

        # Validate each employee
        for emp in employees:
            issues = self._validate_employee(
                emp,
                factory_line_id=factory_line_id,
                hourly_rate=hourly_rate,
                work_start_time=work_start_time,
                work_end_time=work_end_time,
                work_days=work_days,
                break_time_minutes=break_time_minutes,
                dispatch_start_date=dispatch_start_date,
                dispatch_end_date=dispatch_end_date,
            )

            if not issues:
                # No issues = compatible
                compatible.append({
                    "id": emp.id,
                    "employee_number": emp.employee_number,
                    "full_name_kanji": emp.full_name_kanji,
                    "line_name": emp.line_name or "未設定",
                    "status": "compatible"
                })
            else:
                # Has issues = incompatible
                incompatible.append({
                    "id": emp.id,
                    "employee_number": emp.employee_number,
                    "full_name_kanji": emp.full_name_kanji,
                    "line_name": emp.line_name or "未設定",
                    "issues": [
                        {
                            "type": issue.issue_type,
                            "reason": issue.reason,
                            "severity": issue.severity
                        } for issue in issues
                    ]
                })

        # Check if all compatible or some incompatible
        is_valid = len(incompatible) == 0

        # Generate suggestions
        suggestions = self._generate_suggestions(incompatible)

        return {
            "is_valid": is_valid,
            "compatible_count": len(compatible),
            "incompatible_count": len(incompatible),
            "compatible": compatible,
            "incompatible": incompatible,
            "suggestions": suggestions,
            "summary": self._generate_summary(compatible, incompatible)
        }

    def _validate_employee(
        self,
        employee: Employee,
        factory_line_id: Optional[int] = None,
        hourly_rate: Optional[Decimal] = None,
        work_start_time: Optional[time] = None,
        work_end_time: Optional[time] = None,
        work_days: Optional[List[str]] = None,
        break_time_minutes: Optional[int] = None,
        dispatch_start_date: Optional[date] = None,
        dispatch_end_date: Optional[date] = None,
    ) -> List[EmployeeCompatibilityIssue]:
        """
        Check individual employee compatibility.

        Args:
            employee: Employee instance to validate
            factory_line_id: Expected factory line ID
            hourly_rate: Contract hourly rate
            work_start_time: Contract work start time
            work_end_time: Contract work end time
            work_days: Contract work days
            break_time_minutes: Contract break time
            dispatch_start_date: Contract start date
            dispatch_end_date: Contract end date

        Returns:
            List of EmployeeCompatibilityIssue instances
        """
        issues = []

        # 1. Check if employee is active
        if employee.status != "active":
            issues.append(EmployeeCompatibilityIssue(
                employee_id=employee.id,
                employee_number=employee.employee_number,
                employee_name=employee.full_name_kanji,
                line_name=employee.line_name or "未設定",
                issue_type="inactive_employee",
                reason=f"Employee status is '{employee.status}', not 'active'",
                severity="error"
            ))

        # 2. Check if employee is on the expected line
        if factory_line_id is not None and employee.factory_line_id != factory_line_id:
            # Get line name for better error message
            expected_line = "specified line"
            if employee.line_name:
                issues.append(EmployeeCompatibilityIssue(
                    employee_id=employee.id,
                    employee_number=employee.employee_number,
                    employee_name=employee.full_name_kanji,
                    line_name=employee.line_name or "未設定",
                    issue_type="different_line",
                    reason=f"Employee is on '{employee.line_name}' line, but contract expects line ID {factory_line_id}",
                    severity="error"
                ))
            else:
                issues.append(EmployeeCompatibilityIssue(
                    employee_id=employee.id,
                    employee_number=employee.employee_number,
                    employee_name=employee.full_name_kanji,
                    line_name="未設定",
                    issue_type="different_line",
                    reason=f"Employee has no line assigned, but contract expects line ID {factory_line_id}",
                    severity="error"
                ))

        # 3. Check hourly rate (warning only, as rate might change with new contract)
        if hourly_rate is not None and employee.hourly_rate is not None:
            # Convert to Decimal for comparison
            emp_rate = Decimal(str(employee.hourly_rate))
            contract_rate = Decimal(str(hourly_rate))

            if emp_rate != contract_rate:
                # This is a warning, not an error - rate might be changing
                issues.append(EmployeeCompatibilityIssue(
                    employee_id=employee.id,
                    employee_number=employee.employee_number,
                    employee_name=employee.full_name_kanji,
                    line_name=employee.line_name or "未設定",
                    issue_type="different_rate",
                    reason=f"Employee's current rate is ¥{emp_rate}/hr, contract rate is ¥{contract_rate}/hr",
                    severity="warning"
                ))

        # 4. Note: Work schedule validation
        # The contract DEFINES the schedule, so we don't validate against employee's current schedule
        # The schedule parameters are for the NEW contract, not existing employee data

        # 5. Note: Contract period validation
        # Similarly, dispatch dates are for the NEW contract
        # We could add validation for termination_date if needed
        if dispatch_start_date and employee.termination_date:
            if employee.termination_date < dispatch_start_date:
                issues.append(EmployeeCompatibilityIssue(
                    employee_id=employee.id,
                    employee_number=employee.employee_number,
                    employee_name=employee.full_name_kanji,
                    line_name=employee.line_name or "未設定",
                    issue_type="incompatible_schedule",
                    reason=f"Employee's termination date ({employee.termination_date}) is before contract start date ({dispatch_start_date})",
                    severity="error"
                ))

        return issues

    def _generate_suggestions(self, incompatible: List[Dict]) -> List[str]:
        """
        Generate suggestions for handling incompatible employees.

        Args:
            incompatible: List of incompatible employee dicts

        Returns:
            List of suggestion strings
        """
        suggestions = []

        if not incompatible:
            return suggestions

        # Group by issue type
        line_issues = []
        rate_issues = []
        status_issues = []

        for emp in incompatible:
            for issue in emp.get("issues", []):
                if issue["type"] == "different_line":
                    line_issues.append(emp)
                elif issue["type"] == "different_rate":
                    rate_issues.append(emp)
                elif issue["type"] == "inactive_employee":
                    status_issues.append(emp)

        # Generate specific suggestions
        if status_issues:
            suggestions.append(
                f"⚠️ {len(status_issues)} empleado(s) inactivo(s) - Verificar estado antes de crear contrato"
            )

        if line_issues:
            suggestions.append(
                f"📍 {len(line_issues)} empleado(s) en línea diferente - Crear contrato(s) separado(s) por línea"
            )

        if rate_issues and not line_issues:
            # Only suggest rate adjustment if no line issues
            suggestions.append(
                f"💴 {len(rate_issues)} empleado(s) con tarifa diferente - Verificar si es cambio intencional"
            )

        # General suggestion
        if len(incompatible) == 1:
            emp = incompatible[0]
            suggestions.append(
                f"✅ Crear contrato SEPARADO para {emp['full_name_kanji']}"
            )
        elif len(incompatible) > 1:
            suggestions.append(
                f"✅ Crear {len(incompatible)} contrato(s) SEPARADO(s) para empleados con diferentes condiciones"
            )

        return suggestions

    def _generate_summary(self, compatible: List[Dict], incompatible: List[Dict]) -> str:
        """
        Generate summary text.

        Args:
            compatible: List of compatible employee dicts
            incompatible: List of incompatible employee dicts

        Returns:
            Summary string
        """
        if not incompatible:
            if len(compatible) == 1:
                return "✅ 1 empleado compatible"
            else:
                return f"✅ {len(compatible)} empleados pueden agruparse en UN contrato"
        else:
            total = len(compatible) + len(incompatible)
            return (
                f"⚠️ {len(compatible)} compatible(s) + {len(incompatible)} incompatible(s) "
                f"de {total} total → Necesita(n) contrato(s) separado(s)"
            )

    def validate_by_line(
        self,
        employee_ids: List[int]
    ) -> Dict[int, List[int]]:
        """
        Group employees by factory_line_id for separate contracts.

        Args:
            employee_ids: List of employee IDs

        Returns:
            Dictionary mapping factory_line_id to list of employee IDs
            {
                factory_line_id: [employee_id, employee_id, ...],
                ...
            }
        """
        employees = self.db.query(Employee).filter(Employee.id.in_(employee_ids)).all()

        grouped = {}
        no_line = []

        for emp in employees:
            if emp.factory_line_id:
                if emp.factory_line_id not in grouped:
                    grouped[emp.factory_line_id] = []
                grouped[emp.factory_line_id].append(emp.id)
            else:
                no_line.append(emp.id)

        # Add employees without line assignment as separate group
        if no_line:
            grouped[0] = no_line  # 0 = no line assigned

        return grouped
