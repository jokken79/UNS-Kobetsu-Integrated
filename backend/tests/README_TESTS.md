# Backend Test Suite

## Overview

Comprehensive test suite for the UNS-Kobetsu backend API. All tests use SQLite in-memory database for isolation and speed.

## Test Files

### 1. `test_auth_api.py` (217 lines)
Authentication and user management tests:
- **Login tests**: successful login, wrong password, user not found, inactive user
- **Token tests**: token refresh, invalid tokens
- **User registration**: successful registration, duplicate email, weak password
- **Current user**: get user info, unauthorized access
- **Password change**: successful change, wrong current password, weak new password
- **Logout**: successful logout

**Test count**: 16 tests

### 2. `test_factory_api.py` (374 lines)
Factory and factory line CRUD operations:

#### Factory CRUD (11 tests)
- List factories with filters (search, company, pagination)
- Get factory by ID
- Create factory (with/without lines)
- Update factory
- Delete factory (soft delete)

#### Factory Lines (5 tests)
- List lines for a factory
- Create factory line
- Update factory line
- Delete factory line (soft delete)

#### Cascade Dropdowns (7 tests)
- Get company options
- Get plant options by company
- Get department options by factory
- Get line options by factory/department
- Get complete cascade data for a line

**Test count**: 23 tests

### 3. `test_employee_api.py` (443 lines)
Employee management, statistics, and assignments:

#### Employee CRUD (14 tests)
- List employees with filters (search, status, company, factory, nationality, visa expiring)
- Get employee by ID
- Create employee
- Update employee
- Delete employee (soft delete)
- Pagination

#### Employee Statistics (4 tests)
- Get overall stats
- Stats by company
- Stats by nationality
- Age calculations

#### Contract Selection (4 tests)
- Get employees for contract
- Filter by factory
- Search employees
- Exclude specific employees

#### Employee Assignment (4 tests)
- Assign employee to factory
- Unassign employee
- Bulk assign multiple employees
- Assignment validation

#### Visa Management (2 tests)
- Get employees with expiring visas
- Custom day range filter

**Test count**: 28 tests

### 4. `conftest.py` (Improved)
Pytest fixtures for all tests:
- `db`: Fresh SQLite in-memory database for each test
- `test_user`: Active admin user
- `test_inactive_user`: Inactive user for testing
- `client`: FastAPI TestClient with database override
- `auth_headers`: JWT authentication headers
- `test_factory`: Sample factory
- `test_factory_line`: Sample factory line
- `test_employee`: Sample employee (Japanese)
- `test_employee_2`: Second employee (Vietnamese, expiring visa)
- `sample_contract_data`: Contract creation data
- `sample_update_data`: Contract update data

## Running Tests

### Run All Tests
```bash
docker exec -it uns-kobetsu-backend pytest -v
```

### Run Specific Test File
```bash
# Authentication tests
docker exec -it uns-kobetsu-backend pytest tests/test_auth_api.py -v

# Factory tests
docker exec -it uns-kobetsu-backend pytest tests/test_factory_api.py -v

# Employee tests
docker exec -it uns-kobetsu-backend pytest tests/test_employee_api.py -v
```

### Run Specific Test Class
```bash
docker exec -it uns-kobetsu-backend pytest tests/test_factory_api.py::TestFactoryCRUD -v
docker exec -it uns-kobetsu-backend pytest tests/test_employee_api.py::TestEmployeeStats -v
```

### Run Specific Test
```bash
docker exec -it uns-kobetsu-backend pytest tests/test_auth_api.py::TestAuthAPI::test_login_successful -v
```

### Run with Coverage
```bash
docker exec -it uns-kobetsu-backend pytest --cov=app --cov-report=term-missing -v
docker exec -it uns-kobetsu-backend pytest --cov=app --cov-report=html
```

### Run Tests Matching Pattern
```bash
# All login tests
docker exec -it uns-kobetsu-backend pytest -k "login" -v

# All CRUD tests
docker exec -it uns-kobetsu-backend pytest -k "crud" -v

# All stats tests
docker exec -it uns-kobetsu-backend pytest -k "stats" -v
```

## Test Summary

| File | Tests | Coverage |
|------|-------|----------|
| `test_auth_api.py` | 16 | Login, registration, token management |
| `test_factory_api.py` | 23 | Factory CRUD, lines, cascade dropdowns |
| `test_employee_api.py` | 28 | Employee CRUD, stats, assignments, visa |
| **TOTAL** | **67** | **Full API coverage** |

## Test Characteristics

### Isolation
- Each test uses a fresh SQLite in-memory database
- No test dependencies or shared state
- Tests can run in any order

### Speed
- SQLite in-memory is extremely fast
- No need for database cleanup
- Full suite runs in seconds

### Independence
- No external services required
- No real database connections
- No network calls (mocked if needed)

### Coverage
All major API endpoints are tested:
- ✅ Authentication & authorization
- ✅ User management
- ✅ Factory CRUD operations
- ✅ Factory line management
- ✅ Cascade dropdown endpoints
- ✅ Employee CRUD operations
- ✅ Employee statistics
- ✅ Employee assignments
- ✅ Visa expiration tracking
- ✅ Bulk operations

## Example Test Output

```
============================= test session starts ==============================
collected 67 items

tests/test_auth_api.py::TestAuthAPI::test_login_successful PASSED        [  1%]
tests/test_auth_api.py::TestAuthAPI::test_login_wrong_password PASSED    [  2%]
tests/test_auth_api.py::TestAuthAPI::test_get_current_user PASSED        [  4%]
...
tests/test_factory_api.py::TestFactoryCRUD::test_list_factories PASSED   [ 35%]
tests/test_factory_api.py::TestFactoryCRUD::test_create_factory PASSED   [ 37%]
...
tests/test_employee_api.py::TestEmployeeStats::test_get_employee_stats PASSED [ 89%]
tests/test_employee_api.py::TestEmployeeVisa::test_get_employees_with_expiring_visa PASSED [ 98%]

========================== 67 passed in 2.34s ===============================
```

## CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
- name: Run Backend Tests
  run: |
    docker exec uns-kobetsu-backend pytest -v --cov=app --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Next Steps

1. **Add integration tests** for contract creation workflow
2. **Add API documentation tests** to ensure OpenAPI spec matches implementation
3. **Add performance tests** for large dataset queries
4. **Add security tests** for authorization edge cases
5. **Add E2E tests** combining multiple API calls
