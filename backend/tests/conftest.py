"""
Pytest configuration and fixtures for backend tests.
"""
import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from typing import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.factory import Factory, FactoryLine
from app.models.employee import Employee


# Test database URL (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db: Session) -> User:
    """Create a test user in the database."""
    user = User(
        id=1,
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_inactive_user(db: Session) -> User:
    """Create an inactive test user."""
    user = User(
        id=2,
        email="inactive@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Inactive User",
        role="user",
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def client(db: Session, test_user: User) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test requests."""
    token = create_access_token({
        "sub": str(test_user.id),
        "email": test_user.email,
        "role": test_user.role,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_factory(db: Session) -> Factory:
    """Create a test factory."""
    factory = Factory(
        id=1,
        factory_id="テスト株式会社__本社工場",
        company_name="テスト株式会社",
        plant_name="本社工場",
        company_address="東京都千代田区丸の内1-1-1",
        plant_address="東京都千代田区丸の内1-1-1",
        company_phone="03-1234-5678",
        conflict_date=date(2024, 1, 1),
        is_active=True,
    )
    db.add(factory)
    db.commit()
    db.refresh(factory)
    return factory


@pytest.fixture
def test_factory_line(db: Session, test_factory: Factory) -> FactoryLine:
    """Create a test factory line."""
    line = FactoryLine(
        id=1,
        factory_id=test_factory.id,
        line_id="LINE001",
        department="製造部",
        line_name="第1ライン",
        job_description="製造作業",
        hourly_rate=Decimal("1500"),
        billing_rate=Decimal("2000"),
        supervisor_name="田中太郎",
        supervisor_department="製造部",
        supervisor_phone="03-1234-5678",
        is_active=True,
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


@pytest.fixture
def test_employee(db: Session, test_factory: Factory) -> Employee:
    """Create a test employee."""
    employee = Employee(
        id=1,
        employee_number="EMP001",
        full_name_kanji="山田太郎",
        full_name_kana="ヤマダタロウ",
        gender="male",
        nationality="日本",
        date_of_birth=date(1990, 1, 1),
        status="active",
        factory_id=test_factory.id,
        company_name=test_factory.company_name,
        plant_name=test_factory.plant_name,
        hourly_rate=Decimal("1500"),
        billing_rate=Decimal("2000"),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@pytest.fixture
def test_employee_2(db: Session, test_factory: Factory) -> Employee:
    """Create a second test employee."""
    employee = Employee(
        id=2,
        employee_number="EMP002",
        full_name_kanji="佐藤花子",
        full_name_kana="サトウハナコ",
        gender="female",
        nationality="ベトナム",
        date_of_birth=date(1995, 5, 15),
        status="active",
        factory_id=test_factory.id,
        company_name=test_factory.company_name,
        plant_name=test_factory.plant_name,
        visa_expiry_date=date.today() + timedelta(days=20),
        hourly_rate=Decimal("1400"),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@pytest.fixture
def sample_contract_data() -> dict:
    """Sample contract data for testing."""
    return {
        "factory_id": 1,
        "employee_ids": [1, 2],
        "contract_date": str(date.today()),
        "dispatch_start_date": "2024-12-01",
        "dispatch_end_date": "2025-11-30",
        "work_content": "製造ライン作業、検品、梱包業務の補助作業",
        "responsibility_level": "通常業務",
        "worksite_name": "テスト株式会社 本社工場",
        "worksite_address": "東京都千代田区丸の内1-1-1",
        "organizational_unit": "第1製造部",
        "supervisor_department": "製造部",
        "supervisor_position": "課長",
        "supervisor_name": "田中太郎",
        "work_days": ["月", "火", "水", "木", "金"],
        "work_start_time": "08:00",
        "work_end_time": "17:00",
        "break_time_minutes": 60,
        "overtime_max_hours_day": 3,
        "overtime_max_hours_month": 45,
        "hourly_rate": 1500,
        "overtime_rate": 1875,
        "haken_moto_complaint_contact": {
            "department": "人事部",
            "position": "課長",
            "name": "山田花子",
            "phone": "03-1234-5678",
        },
        "haken_saki_complaint_contact": {
            "department": "総務部",
            "position": "係長",
            "name": "佐藤次郎",
            "phone": "03-9876-5432",
        },
        "haken_moto_manager": {
            "department": "派遣事業部",
            "position": "部長",
            "name": "鈴木一郎",
            "phone": "03-1234-5678",
        },
        "haken_saki_manager": {
            "department": "人事部",
            "position": "部長",
            "name": "高橋三郎",
            "phone": "03-9876-5432",
        },
    }


@pytest.fixture
def sample_update_data() -> dict:
    """Sample update data for testing."""
    return {
        "work_content": "更新された業務内容です。新しい作業が追加されました。",
        "hourly_rate": 1600,
        "notes": "テスト更新",
    }
