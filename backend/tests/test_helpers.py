"""
Test API Helper Functions

Tests for the validation helpers to ensure they work correctly after refactoring.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, Mock

from app.api.v1.helpers import (
    get_contract_or_404,
    get_employee_or_404,
    get_factory_or_404,
    validate_contract_status,
    validate_date_range,
    validate_employee_not_in_contract,
)
from app.models.kobetsu_keiyakusho import KobetsuKeiyakusho, KobetsuEmployee
from app.models.employee import Employee
from app.models.factory import Factory
from datetime import date


def test_get_contract_or_404_found():
    """Test get_contract_or_404 when contract exists."""
    # Mock database session
    db = MagicMock(spec=Session)

    # Mock contract
    mock_contract = MagicMock(spec=KobetsuKeiyakusho)
    mock_contract.id = 1

    # Setup query chain
    db.query.return_value.filter.return_value.first.return_value = mock_contract

    # Call function
    result = get_contract_or_404(db, 1)

    # Assertions
    assert result == mock_contract
    db.query.assert_called_once_with(KobetsuKeiyakusho)


def test_get_contract_or_404_not_found():
    """Test get_contract_or_404 when contract doesn't exist."""
    # Mock database session
    db = MagicMock(spec=Session)

    # Setup query to return None
    db.query.return_value.filter.return_value.first.return_value = None

    # Call function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        get_contract_or_404(db, 999)

    assert exc_info.value.status_code == 404
    assert "Contract with ID 999 not found" in str(exc_info.value.detail)


def test_get_employee_or_404_found():
    """Test get_employee_or_404 when employee exists."""
    # Mock database session
    db = MagicMock(spec=Session)

    # Mock employee
    mock_employee = MagicMock(spec=Employee)
    mock_employee.id = 1

    # Setup query chain
    db.query.return_value.filter.return_value.first.return_value = mock_employee

    # Call function
    result = get_employee_or_404(db, 1)

    # Assertions
    assert result == mock_employee
    db.query.assert_called_once_with(Employee)


def test_get_factory_or_404_found():
    """Test get_factory_or_404 when factory exists."""
    # Mock database session
    db = MagicMock(spec=Session)

    # Mock factory
    mock_factory = MagicMock(spec=Factory)
    mock_factory.id = 1

    # Setup query chain
    db.query.return_value.filter.return_value.first.return_value = mock_factory

    # Call function
    result = get_factory_or_404(db, 1)

    # Assertions
    assert result == mock_factory
    db.query.assert_called_once_with(Factory)


def test_validate_contract_status_valid():
    """Test validate_contract_status with valid status."""
    # Mock contract with draft status
    mock_contract = MagicMock(spec=KobetsuKeiyakusho)
    mock_contract.status = "draft"

    # Should not raise exception
    validate_contract_status(mock_contract, ["draft", "active"])


def test_validate_contract_status_invalid():
    """Test validate_contract_status with invalid status."""
    # Mock contract with active status
    mock_contract = MagicMock(spec=KobetsuKeiyakusho)
    mock_contract.status = "active"

    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_contract_status(mock_contract, ["draft"], "Cannot modify active contract")

    assert exc_info.value.status_code == 400
    assert "Cannot modify active contract" in str(exc_info.value.detail)
    assert "active" in str(exc_info.value.detail)
    assert "draft" in str(exc_info.value.detail)


def test_validate_date_range_valid():
    """Test validate_date_range with valid dates."""
    start = date(2025, 1, 1)
    end = date(2025, 12, 31)

    # Should not raise exception
    validate_date_range(start, end)


def test_validate_date_range_invalid():
    """Test validate_date_range with invalid dates."""
    start = date(2025, 12, 31)
    end = date(2025, 1, 1)

    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_date_range(start, end, "contract")

    assert exc_info.value.status_code == 400
    assert "Invalid contract range" in str(exc_info.value.detail)


def test_validate_employee_not_in_contract_not_exists():
    """Test validate_employee_not_in_contract when employee is not in contract."""
    # Mock database session
    db = MagicMock(spec=Session)

    # Setup query to return None (employee not in contract)
    db.query.return_value.filter.return_value.first.return_value = None

    # Call function
    result = validate_employee_not_in_contract(db, 1, 100)

    # Assertions
    assert result is True
    db.query.assert_called_once_with(KobetsuEmployee)


def test_validate_employee_not_in_contract_exists():
    """Test validate_employee_not_in_contract when employee is already in contract."""
    # Mock database session
    db = MagicMock(spec=Session)

    # Mock existing relationship
    mock_relation = MagicMock(spec=KobetsuEmployee)

    # Setup query to return existing relationship
    db.query.return_value.filter.return_value.first.return_value = mock_relation

    # Call function
    result = validate_employee_not_in_contract(db, 1, 100)

    # Assertions
    assert result is False