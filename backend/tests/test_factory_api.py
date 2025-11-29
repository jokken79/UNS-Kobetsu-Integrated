"""
Factory API Tests - /api/v1/factories endpoints
"""
import pytest
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.factory import Factory, FactoryLine


class TestFactoryCRUD:
    """Test suite for factory CRUD operations."""

    def test_list_factories(self, client: TestClient, auth_headers: dict, test_factory: Factory):
        """Test listing factories."""
        response = client.get("/api/v1/factories", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["company_name"] == test_factory.company_name

    def test_list_factories_with_search(self, client: TestClient, auth_headers: dict, test_factory: Factory):
        """Test factory search filter."""
        response = client.get(
            "/api/v1/factories",
            headers=auth_headers,
            params={"search": "テスト"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_factories_by_company(self, client: TestClient, auth_headers: dict, test_factory: Factory):
        """Test filtering factories by company name."""
        response = client.get(
            "/api/v1/factories",
            headers=auth_headers,
            params={"company_name": test_factory.company_name}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(f["company_name"] == test_factory.company_name for f in data)

    def test_list_factories_pagination(self, client: TestClient, auth_headers: dict, test_factory: Factory):
        """Test factory list pagination."""
        response = client.get(
            "/api/v1/factories",
            headers=auth_headers,
            params={"skip": 0, "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

    def test_get_factory_by_id(self, client: TestClient, auth_headers: dict, test_factory: Factory):
        """Test retrieving a single factory by ID."""
        response = client.get(f"/api/v1/factories/{test_factory.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_factory.id
        assert data["company_name"] == test_factory.company_name
        assert data["plant_name"] == test_factory.plant_name

    def test_get_factory_not_found(self, client: TestClient, auth_headers: dict):
        """Test retrieving non-existent factory returns 404."""
        response = client.get("/api/v1/factories/99999", headers=auth_headers)
        
        assert response.status_code == 404

    def test_create_factory(self, client: TestClient, auth_headers: dict, db: Session):
        """Test creating a new factory."""
        factory_data = {
            "factory_id": "新会社__新工場",
            "company_name": "新会社株式会社",
            "plant_name": "新工場",
            "company_address": "大阪府大阪市北区梅田1-1-1",
            "plant_address": "大阪府大阪市北区梅田1-1-1",
            "company_phone": "06-1234-5678",
            "is_active": True
        }
        
        response = client.post("/api/v1/factories/", headers=auth_headers, json=factory_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == factory_data["company_name"]
        assert data["plant_name"] == factory_data["plant_name"]
        
        # Verify in database
        factory = db.query(Factory).filter(Factory.factory_id == factory_data["factory_id"]).first()
        assert factory is not None

    def test_create_factory_duplicate(self, client: TestClient, auth_headers: dict, test_factory: Factory):
        """Test creating factory with duplicate ID fails."""
        factory_data = {
            "factory_id": test_factory.factory_id,  # Duplicate
            "company_name": "重複会社",
            "plant_name": "重複工場"
        }
        
        response = client.post("/api/v1/factories/", headers=auth_headers, json=factory_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_factory_with_lines(self, client: TestClient, auth_headers: dict):
        """Test creating factory with factory lines."""
        factory_data = {
            "factory_id": "ライン付き__工場",
            "company_name": "ライン付き株式会社",
            "plant_name": "ライン付き工場",
            "lines": [
                {
                    "line_id": "LINE001",
                    "department": "製造部",
                    "line_name": "第1ライン",
                    "job_description": "組立作業",
                    "hourly_rate": 1500
                }
            ]
        }
        
        response = client.post("/api/v1/factories/", headers=auth_headers, json=factory_data)
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["lines"]) == 1

    def test_update_factory(self, client: TestClient, auth_headers: dict, test_factory: Factory, db: Session):
        """Test updating a factory."""
        update_data = {
            "company_address": "更新された住所",
            "company_phone": "03-9999-9999"
        }
        
        response = client.put(
            f"/api/v1/factories/{test_factory.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_address"] == update_data["company_address"]
        
        # Verify in database
        db.refresh(test_factory)
        assert test_factory.company_address == update_data["company_address"]

    def test_update_factory_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent factory returns 404."""
        response = client.put(
            "/api/v1/factories/99999",
            headers=auth_headers,
            json={"company_name": "更新"}
        )
        
        assert response.status_code == 404

    def test_delete_factory(self, client: TestClient, auth_headers: dict, db: Session):
        """Test soft deleting a factory."""
        # Create a factory to delete
        factory = Factory(
            factory_id="削除テスト__工場",
            company_name="削除テスト株式会社",
            plant_name="削除テスト工場",
            is_active=True
        )
        db.add(factory)
        db.commit()
        db.refresh(factory)
        
        response = client.delete(f"/api/v1/factories/{factory.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify soft delete
        db.refresh(factory)
        assert factory.is_active is False

    def test_delete_factory_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent factory returns 404."""
        response = client.delete("/api/v1/factories/99999", headers=auth_headers)
        
        assert response.status_code == 404


class TestFactoryLines:
    """Test suite for factory line operations."""

    def test_list_factory_lines(self, client: TestClient, auth_headers: dict, test_factory: Factory, test_factory_line: FactoryLine):
        """Test listing lines for a factory."""
        response = client.get(
            f"/api/v1/factories/{test_factory.id}/lines",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_factory_lines_not_found(self, client: TestClient, auth_headers: dict):
        """Test listing lines for non-existent factory."""
        response = client.get("/api/v1/factories/99999/lines", headers=auth_headers)
        
        assert response.status_code == 404

    def test_create_factory_line(self, client: TestClient, auth_headers: dict, test_factory: Factory, db: Session):
        """Test creating a new factory line."""
        line_data = {
            "line_id": "LINE002",
            "department": "検査部",
            "line_name": "検査ライン",
            "job_description": "品質検査",
            "hourly_rate": 1600,
            "supervisor_name": "鈴木花子"
        }
        
        response = client.post(
            f"/api/v1/factories/{test_factory.id}/lines",
            headers=auth_headers,
            json=line_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["line_id"] == line_data["line_id"]
        assert data["department"] == line_data["department"]

    def test_update_factory_line(self, client: TestClient, auth_headers: dict, test_factory_line: FactoryLine, db: Session):
        """Test updating a factory line."""
        update_data = {
            "hourly_rate": 1700,
            "supervisor_name": "更新担当者"
        }
        
        response = client.put(
            f"/api/v1/factories/lines/{test_factory_line.id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert float(data["hourly_rate"]) == update_data["hourly_rate"]

    def test_delete_factory_line(self, client: TestClient, auth_headers: dict, db: Session, test_factory: Factory):
        """Test soft deleting a factory line."""
        # Create a line to delete
        line = FactoryLine(
            factory_id=test_factory.id,
            line_id="DEL001",
            department="削除部",
            line_name="削除ライン",
            is_active=True
        )
        db.add(line)
        db.commit()
        db.refresh(line)
        
        response = client.delete(f"/api/v1/factories/lines/{line.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify soft delete
        db.refresh(line)
        assert line.is_active is False


class TestFactoryCascadeDropdowns:
    """Test suite for cascade dropdown endpoints."""

    def test_get_company_options(self, client: TestClient, auth_headers: dict, test_factory: Factory):
        """Test getting company options for dropdown."""
        response = client.get("/api/v1/factories/dropdown/companies", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(c["company_name"] == test_factory.company_name for c in data)

    def test_get_company_options_search(self, client: TestClient, auth_headers: dict, test_factory: Factory):
        """Test searching company options."""
        response = client.get(
            "/api/v1/factories/dropdown/companies",
            headers=auth_headers,
            params={"search": "テスト"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_get_plant_options(self, client: TestClient, auth_headers: dict, test_factory: Factory):
        """Test getting plant options for a company."""
        response = client.get(
            "/api/v1/factories/dropdown/plants",
            headers=auth_headers,
            params={"company_name": test_factory.company_name}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_department_options(self, client: TestClient, auth_headers: dict, test_factory: Factory, test_factory_line: FactoryLine):
        """Test getting department options for a factory."""
        response = client.get(
            "/api/v1/factories/dropdown/departments",
            headers=auth_headers,
            params={"factory_id": test_factory.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_line_options(self, client: TestClient, auth_headers: dict, test_factory: Factory, test_factory_line: FactoryLine):
        """Test getting line options for a factory."""
        response = client.get(
            "/api/v1/factories/dropdown/lines",
            headers=auth_headers,
            params={"factory_id": test_factory.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_line_options_filtered_by_department(self, client: TestClient, auth_headers: dict, test_factory: Factory, test_factory_line: FactoryLine):
        """Test getting line options filtered by department."""
        response = client.get(
            "/api/v1/factories/dropdown/lines",
            headers=auth_headers,
            params={
                "factory_id": test_factory.id,
                "department": test_factory_line.department
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_cascade_data(self, client: TestClient, auth_headers: dict, test_factory_line: FactoryLine):
        """Test getting complete cascade data for a line."""
        response = client.get(
            f"/api/v1/factories/dropdown/cascade/{test_factory_line.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "factory" in data
        assert "line" in data
        assert data["line"]["id"] == test_factory_line.id

    def test_get_cascade_data_not_found(self, client: TestClient, auth_headers: dict):
        """Test cascade data for non-existent line."""
        response = client.get("/api/v1/factories/dropdown/cascade/99999", headers=auth_headers)
        
        assert response.status_code == 404
