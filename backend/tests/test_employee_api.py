"""
Employee API Tests - /api/v1/employees endpoints
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.factory import Factory


class TestEmployeeCRUD:
    """Test suite for employee CRUD operations."""

    def test_list_employees(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test listing employees."""
        response = client.get("/api/v1/employees", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["employee_number"] == test_employee.employee_number

    def test_list_employees_with_search(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test employee search filter."""
        response = client.get(
            "/api/v1/employees",
            headers=auth_headers,
            params={"search": "山田"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_employees_by_status(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test filtering employees by status."""
        response = client.get(
            "/api/v1/employees",
            headers=auth_headers,
            params={"status": "active"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(e["status"] == "active" for e in data)

    def test_list_employees_by_company(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test filtering employees by company."""
        response = client.get(
            "/api/v1/employees",
            headers=auth_headers,
            params={"company_name": test_employee.company_name}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(e["company_name"] == test_employee.company_name for e in data)

    def test_list_employees_by_factory(self, client: TestClient, auth_headers: dict, test_employee: Employee, test_factory: Factory):
        """Test filtering employees by factory."""
        response = client.get(
            "/api/v1/employees",
            headers=auth_headers,
            params={"factory_id": test_factory.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_employees_by_nationality(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test filtering employees by nationality."""
        response = client.get(
            "/api/v1/employees",
            headers=auth_headers,
            params={"nationality": "日本"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(e["nationality"] == "日本" for e in data)

    def test_list_employees_visa_expiring(self, client: TestClient, auth_headers: dict, test_employee_2: Employee):
        """Test filtering employees by visa expiration."""
        response = client.get(
            "/api/v1/employees",
            headers=auth_headers,
            params={"visa_expiring_days": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_employees_pagination(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test employee list pagination."""
        response = client.get(
            "/api/v1/employees",
            headers=auth_headers,
            params={"skip": 0, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

    def test_get_employee_by_id(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test retrieving a single employee by ID."""
        response = client.get(f"/api/v1/employees/{test_employee.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_employee.id
        assert data["employee_number"] == test_employee.employee_number
        assert data["full_name_kanji"] == test_employee.full_name_kanji

    def test_get_employee_not_found(self, client: TestClient, auth_headers: dict):
        """Test retrieving non-existent employee returns 404."""
        response = client.get("/api/v1/employees/99999", headers=auth_headers)
        
        assert response.status_code == 404

    def test_create_employee(self, client: TestClient, auth_headers: dict, db: Session):
        """Test creating a new employee."""
        employee_data = {
            "employee_number": "EMP999",
            "full_name_kanji": "新規太郎",
            "full_name_kana": "シンキタロウ",
            "gender": "male",
            "nationality": "日本",
            "date_of_birth": "1992-03-15",
            "status": "active"
        }
        
        response = client.post("/api/v1/employees/", headers=auth_headers, json=employee_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["employee_number"] == employee_data["employee_number"]
        assert data["full_name_kanji"] == employee_data["full_name_kanji"]
        
        # Verify in database
        employee = db.query(Employee).filter(
            Employee.employee_number == employee_data["employee_number"]
        ).first()
        assert employee is not None

    def test_create_employee_duplicate_number(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test creating employee with duplicate number fails."""
        employee_data = {
            "employee_number": test_employee.employee_number,  # Duplicate
            "full_name_kanji": "重複太郎",
            "full_name_kana": "チョウフクタロウ",
            "gender": "male",
            "nationality": "日本",
            "status": "active"
        }
        
        response = client.post("/api/v1/employees/", headers=auth_headers, json=employee_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_update_employee(self, client: TestClient, auth_headers: dict, test_employee: Employee, db: Session):
        """Test updating an employee."""
        update_data = {
            "full_name_kanji": "更新太郎",
            "hourly_rate": 1600
        }
        
        response = client.put(
            f"/api/v1/employees/{test_employee.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name_kanji"] == update_data["full_name_kanji"]
        
        # Verify in database
        db.refresh(test_employee)
        assert test_employee.full_name_kanji == update_data["full_name_kanji"]

    def test_update_employee_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent employee returns 404."""
        response = client.put(
            "/api/v1/employees/99999",
            headers=auth_headers,
            json={"full_name_kanji": "更新"}
        )
        
        assert response.status_code == 404

    def test_delete_employee(self, client: TestClient, auth_headers: dict, db: Session, test_factory: Factory):
        """Test soft deleting an employee."""
        # Create an employee to delete
        employee = Employee(
            employee_number="DEL001",
            full_name_kanji="削除太郎",
            full_name_kana="サクジョタロウ",
            gender="male",
            nationality="日本",
            status="active"
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        
        response = client.delete(f"/api/v1/employees/{employee.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify soft delete
        db.refresh(employee)
        assert employee.status == "resigned"
        assert employee.termination_date is not None

    def test_delete_employee_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent employee returns 404."""
        response = client.delete("/api/v1/employees/99999", headers=auth_headers)
        
        assert response.status_code == 404


class TestEmployeeStats:
    """Test suite for employee statistics."""

    def test_get_employee_stats(self, client: TestClient, auth_headers: dict, test_employee: Employee, test_employee_2: Employee):
        """Test retrieving employee statistics."""
        response = client.get("/api/v1/employees/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_employees" in data
        assert "active_employees" in data
        assert "resigned_employees" in data
        assert "visa_expiring_soon" in data
        assert data["total_employees"] >= 2

    def test_stats_by_company(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test employee stats include company breakdown."""
        response = client.get("/api/v1/employees/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "by_company" in data
        assert isinstance(data["by_company"], list)

    def test_stats_by_nationality(self, client: TestClient, auth_headers: dict, test_employee: Employee, test_employee_2: Employee):
        """Test employee stats include nationality breakdown."""
        response = client.get("/api/v1/employees/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "by_nationality" in data
        assert isinstance(data["by_nationality"], list)

    def test_stats_age_calculations(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test employee stats include age calculations."""
        response = client.get("/api/v1/employees/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "average_age" in data
        assert "under_18_count" in data
        assert "over_60_count" in data


class TestEmployeeForContract:
    """Test suite for employee contract selection."""

    def test_get_employees_for_contract(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test getting employees for contract selection."""
        response = client.get("/api/v1/employees/for-contract", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_employees_for_contract_by_factory(self, client: TestClient, auth_headers: dict, test_employee: Employee, test_factory: Factory):
        """Test filtering contract employees by factory."""
        response = client.get(
            "/api/v1/employees/for-contract",
            headers=auth_headers,
            params={"factory_id": test_factory.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_employees_for_contract_search(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test searching employees for contract."""
        response = client.get(
            "/api/v1/employees/for-contract",
            headers=auth_headers,
            params={"search": "山田"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_employees_for_contract_exclude(self, client: TestClient, auth_headers: dict, test_employee: Employee, test_employee_2: Employee):
        """Test excluding employees from contract selection."""
        response = client.get(
            "/api/v1/employees/for-contract",
            headers=auth_headers,
            params={"exclude_ids": f"{test_employee.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert not any(e["id"] == test_employee.id for e in data)


class TestEmployeeAssignment:
    """Test suite for employee factory assignments."""

    def test_assign_employee_to_factory(self, client: TestClient, auth_headers: dict, db: Session, test_factory: Factory):
        """Test assigning an employee to a factory."""
        # Create unassigned employee
        employee = Employee(
            employee_number="UNASSIGNED001",
            full_name_kanji="未配属太郎",
            full_name_kana="ミハイゾクタロウ",
            gender="male",
            nationality="日本",
            status="active"
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        
        assignment_data = {
            "factory_id": test_factory.id,
            "company_name": test_factory.company_name,
            "plant_name": test_factory.plant_name,
            "department": "製造部",
            "hourly_rate": 1500
        }
        
        response = client.post(
            f"/api/v1/employees/{employee.id}/assign",
            headers=auth_headers,
            json=assignment_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["factory_id"] == test_factory.id
        assert data["company_name"] == test_factory.company_name
        
        # Verify in database
        db.refresh(employee)
        assert employee.factory_id == test_factory.id

    def test_assign_employee_factory_not_found(self, client: TestClient, auth_headers: dict, test_employee: Employee):
        """Test assigning to non-existent factory fails."""
        assignment_data = {
            "factory_id": 99999,
            "company_name": "存在しない"
        }
        
        response = client.post(
            f"/api/v1/employees/{test_employee.id}/assign",
            headers=auth_headers,
            json=assignment_data
        )
        
        assert response.status_code == 404

    def test_unassign_employee(self, client: TestClient, auth_headers: dict, test_employee: Employee, db: Session):
        """Test removing employee factory assignment."""
        response = client.post(
            f"/api/v1/employees/{test_employee.id}/unassign",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["factory_id"] is None
        assert data["company_name"] is None
        
        # Verify in database
        db.refresh(test_employee)
        assert test_employee.factory_id is None

    def test_bulk_assign_employees(self, client: TestClient, auth_headers: dict, test_employee: Employee, test_employee_2: Employee, test_factory: Factory):
        """Test bulk assigning multiple employees."""
        assignment_data = {
            "factory_id": test_factory.id,
            "company_name": test_factory.company_name,
            "department": "製造部"
        }
        
        response = client.post(
            "/api/v1/employees/bulk/assign",
            headers=auth_headers,
            params={"employee_ids": [test_employee.id, test_employee_2.id]},
            json=assignment_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 2
        assert data["not_found_count"] == 0


class TestEmployeeVisa:
    """Test suite for visa management."""

    def test_get_employees_with_expiring_visa(self, client: TestClient, auth_headers: dict, test_employee_2: Employee):
        """Test retrieving employees with expiring visas."""
        response = client.get(
            "/api/v1/employees/visa/expiring",
            headers=auth_headers,
            params={"days": 30}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # test_employee_2 has visa expiring in 20 days
        assert len(data) >= 1

    def test_get_employees_with_expiring_visa_custom_days(self, client: TestClient, auth_headers: dict, test_employee_2: Employee):
        """Test visa expiration with custom day range."""
        response = client.get(
            "/api/v1/employees/visa/expiring",
            headers=auth_headers,
            params={"days": 90}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
