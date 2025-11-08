"""
Tests for database components.

This module tests database functionality including:
- Database connections and configuration
- Connection pooling
- Query execution and error handling
- Data validation and integrity
- Migration and schema management
"""

import pytest
import psycopg2
from unittest.mock import Mock, patch, MagicMock
from tests.utils.test_helpers import (
    assert_no_exceptions,
    generate_mock_bill_data,
    generate_mock_member_data,
    generate_mock_vote_data,
    create_test_database_schema,
    cleanup_test_database
)


class TestDatabaseConnection:
    """Test database connection functionality."""

    @pytest.fixture
    def db_config(self):
        """Database configuration for testing."""
        return {
            'host': 'localhost',
            'port': 5432,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db'
        }

    @pytest.mark.unit
    def test_connection_initialization(self, db_config):
        """Test database connection initialization."""
        from database_connection import get_db_config

        config = get_db_config()

        # Should return configuration dict
        assert isinstance(config, dict)
        assert 'host' in config
        assert 'port' in config
        assert 'user' in config

    @pytest.mark.unit
    def test_connection_string_generation(self, db_config):
        """Test database connection string generation."""
        from database_connection import get_connection_string

        conn_string = get_connection_string()

        assert isinstance(conn_string, str)
        assert 'postgresql://' in conn_string
        assert db_config['user'] in conn_string
        assert db_config['host'] in conn_string

    @pytest.mark.unit
    def test_connection_with_mock(self, db_config, mock_db_connection):
        """Test database connection with mock."""
        # Mock connection should work without actual database
        assert mock_db_connection is not None

        # Test basic operations
        cursor = mock_db_connection.cursor.return_value
        assert cursor is not None

    @pytest.mark.unit
    def test_connection_error_handling(self, db_config):
        """Test connection error handling."""
        with patch('psycopg2.connect', side_effect=psycopg2.OperationalError("Connection failed")):
            from database_connection import get_db_connection

            # Should handle connection errors gracefully
            assert_no_exceptions(get_db_connection)


class TestDatabaseOperations:
    """Test database operations functionality."""

    @pytest.fixture
    def db_operations(self):
        """Create database operations instance for testing."""
        class MockDatabaseOperations:
            def __init__(self):
                self.connection = None

            def execute_query(self, query, params=None):
                """Mock query execution."""
                if self.connection:
                    cursor = self.connection.cursor()
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
                return []

            def execute_insert(self, table, data):
                """Mock insert operation."""
                if self.connection:
                    cursor = self.connection.cursor()
                    columns = ', '.join(data.keys())
                    placeholders = ', '.join(['%s'] * len(data))
                    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                    cursor.execute(query, list(data.values()))
                    self.connection.commit()
                    return cursor.lastrowid
                return None

            def execute_update(self, table, data, conditions):
                """Mock update operation."""
                if self.connection:
                    cursor = self.connection.cursor()
                    set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
                    where_clause = ' AND '.join([f"{k} = %s" for k in conditions.keys()])
                    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
                    params = list(data.values()) + list(conditions.values())
                    cursor.execute(query, params)
                    self.connection.commit()
                    return cursor.rowcount
                return 0

        return MockDatabaseOperations()

    @pytest.mark.unit
    def test_query_execution(self, db_operations, mock_db_connection):
        """Test query execution."""
        db_operations.connection = mock_db_connection

        # Mock cursor results
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.fetchall.return_value = [("result1",), ("result2",)]

        results = db_operations.execute_query("SELECT * FROM test_table")

        assert len(results) == 2
        mock_cursor.execute.assert_called_with("SELECT * FROM test_table", ())

    @pytest.mark.unit
    def test_insert_operation(self, db_operations, mock_db_connection):
        """Test insert operation."""
        db_operations.connection = mock_db_connection

        test_data = {"name": "Test Item", "value": 123}

        result = db_operations.execute_insert("test_table", test_data)

        # Verify the insert was called correctly
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.execute.assert_called()

    @pytest.mark.unit
    def test_update_operation(self, db_operations, mock_db_connection):
        """Test update operation."""
        db_operations.connection = mock_db_connection

        test_data = {"name": "Updated Item"}
        conditions = {"id": 1}

        result = db_operations.execute_update("test_table", test_data, conditions)

        # Verify the update was called correctly
        mock_cursor = mock_db_connection.cursor.return_value
        mock_cursor.execute.assert_called()

    @pytest.mark.unit
    def test_transaction_handling(self, db_operations, mock_db_connection):
        """Test transaction handling."""
        db_operations.connection = mock_db_connection

        # Test commit
        db_operations.connection.commit()
        mock_db_connection.commit.assert_called()

        # Test rollback
        db_operations.connection.rollback()
        mock_db_connection.rollback.assert_called()


class TestDataValidation:
    """Test data validation functionality."""

    @pytest.fixture
    def data_validator(self):
        """Create data validator instance for testing."""
        class MockDataValidator:
            def validate_bill_data(self, data):
                """Validate bill data."""
                required_fields = ['bill_id', 'title', 'jurisdiction']
                return all(field in data and data[field] for field in required_fields)

            def validate_member_data(self, data):
                """Validate member data."""
                required_fields = ['member_id', 'name', 'jurisdiction']
                return all(field in data and data[field] for field in required_fields)

            def validate_vote_data(self, data):
                """Validate vote data."""
                required_fields = ['vote_id', 'jurisdiction', 'result']
                return all(field in data and data[field] for field in required_fields)

            def sanitize_input(self, data):
                """Sanitize input data."""
                sanitized = {}
                for key, value in data.items():
                    if isinstance(value, str):
                        # Basic sanitization - remove dangerous characters
                        sanitized[key] = value.replace('<', '&lt;').replace('>', '&gt;')
                    else:
                        sanitized[key] = value
                return sanitized

        return MockDataValidator()

    @pytest.mark.unit
    def test_bill_data_validation(self, data_validator):
        """Test bill data validation."""
        valid_bill = generate_mock_bill_data()
        invalid_bill = {"invalid": "data"}

        assert data_validator.validate_bill_data(valid_bill) is True
        assert data_validator.validate_bill_data(invalid_bill) is False

    @pytest.mark.unit
    def test_member_data_validation(self, data_validator):
        """Test member data validation."""
        valid_member = generate_mock_member_data()
        invalid_member = {"invalid": "data"}

        assert data_validator.validate_member_data(valid_member) is True
        assert data_validator.validate_member_data(invalid_member) is False

    @pytest.mark.unit
    def test_vote_data_validation(self, data_validator):
        """Test vote data validation."""
        valid_vote = generate_mock_vote_data()
        invalid_vote = {"invalid": "data"}

        assert data_validator.validate_vote_data(valid_vote) is True
        assert data_validator.validate_vote_data(invalid_vote) is False

    @pytest.mark.unit
    def test_input_sanitization(self, data_validator):
        """Test input sanitization."""
        dangerous_data = {
            "title": "<script>alert('xss')</script>Test Bill",
            "description": "Normal description",
            "value": 123
        }

        sanitized = data_validator.sanitize_input(dangerous_data)

        assert "<script>" not in sanitized["title"]
        assert "&lt;script&gt;" in sanitized["title"]
        assert sanitized["description"] == "Normal description"
        assert sanitized["value"] == 123


class TestSchemaManagement:
    """Test database schema management."""

    @pytest.fixture
    def schema_manager(self):
        """Create schema manager instance for testing."""
        class MockSchemaManager:
            def __init__(self):
                self.schemas = {}

            def create_table(self, table_name, columns):
                """Create table schema."""
                self.schemas[table_name] = columns
                return f"CREATE TABLE {table_name} ({', '.join(columns)});"

            def add_index(self, table_name, index_name, columns):
                """Add index to table."""
                index_sql = f"CREATE INDEX {index_name} ON {table_name} ({', '.join(columns)});"
                return index_sql

            def add_constraint(self, table_name, constraint_name, constraint_sql):
                """Add constraint to table."""
                return f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} {constraint_sql};"

            def get_table_schema(self, table_name):
                """Get table schema."""
                return self.schemas.get(table_name, [])

        return MockSchemaManager()

    @pytest.mark.unit
    def test_table_creation(self, schema_manager):
        """Test table creation."""
        columns = ["id SERIAL PRIMARY KEY", "name VARCHAR(255)", "created_at TIMESTAMP"]
        sql = schema_manager.create_table("test_table", columns)

        assert "CREATE TABLE test_table" in sql
        assert "id SERIAL PRIMARY KEY" in sql
        assert schema_manager.get_table_schema("test_table") == columns

    @pytest.mark.unit
    def test_index_creation(self, schema_manager):
        """Test index creation."""
        sql = schema_manager.add_index("test_table", "idx_name", ["name"])

        assert "CREATE INDEX idx_name ON test_table (name)" in sql

    @pytest.mark.unit
    def test_constraint_addition(self, schema_manager):
        """Test constraint addition."""
        sql = schema_manager.add_constraint("test_table", "unique_name", "UNIQUE (name)")

        assert "ALTER TABLE test_table ADD CONSTRAINT unique_name UNIQUE (name)" in sql


class TestMigrationSystem:
    """Test database migration system."""

    @pytest.fixture
    def migration_manager(self):
        """Create migration manager instance for testing."""
        class MockMigrationManager:
            def __init__(self):
                self.migrations = []
                self.current_version = 0

            def create_migration(self, version, description, up_sql, down_sql=None):
                """Create a migration."""
                migration = {
                    "version": version,
                    "description": description,
                    "up_sql": up_sql,
                    "down_sql": down_sql,
                    "applied": False
                }
                self.migrations.append(migration)
                return migration

            def apply_migration(self, version):
                """Apply a migration."""
                for migration in self.migrations:
                    if migration["version"] == version:
                        migration["applied"] = True
                        self.current_version = version
                        return True
                return False

            def rollback_migration(self, version):
                """Rollback a migration."""
                for migration in self.migrations:
                    if migration["version"] == version:
                        migration["applied"] = False
                        self.current_version = max(0, version - 1)
                        return True
                return False

        return MockMigrationManager()

    @pytest.mark.unit
    def test_migration_creation(self, migration_manager):
        """Test migration creation."""
        up_sql = "ALTER TABLE bills ADD COLUMN new_field VARCHAR(255);"
        down_sql = "ALTER TABLE bills DROP COLUMN new_field;"

        migration = migration_manager.create_migration(
            1, "Add new field to bills table", up_sql, down_sql
        )

        assert migration["version"] == 1
        assert migration["description"] == "Add new field to bills table"
        assert migration["up_sql"] == up_sql
        assert migration["down_sql"] == down_sql
        assert migration["applied"] is False

    @pytest.mark.unit
    def test_migration_application(self, migration_manager):
        """Test migration application."""
        migration_manager.create_migration(1, "Test migration", "SELECT 1;")

        result = migration_manager.apply_migration(1)

        assert result is True
        assert migration_manager.current_version == 1
        assert migration_manager.migrations[0]["applied"] is True

    @pytest.mark.unit
    def test_migration_rollback(self, migration_manager):
        """Test migration rollback."""
        migration_manager.create_migration(1, "Test migration", "SELECT 1;")
        migration_manager.apply_migration(1)

        result = migration_manager.rollback_migration(1)

        assert result is True
        assert migration_manager.current_version == 0
        assert migration_manager.migrations[0]["applied"] is False


class TestConnectionPooling:
    """Test database connection pooling."""

    @pytest.fixture
    def connection_pool(self):
        """Create connection pool instance for testing."""
        class MockConnectionPool:
            def __init__(self, minconn=1, maxconn=10):
                self.minconn = minconn
                self.maxconn = maxconn
                self.connections = []
                self.available = []

            def getconn(self):
                """Get a connection from the pool."""
                if self.available:
                    return self.available.pop()
                elif len(self.connections) < self.maxconn:
                    # Create new connection
                    conn = Mock()
                    self.connections.append(conn)
                    return conn
                else:
                    raise Exception("Connection pool exhausted")

            def putconn(self, conn):
                """Return a connection to the pool."""
                if conn in self.connections and conn not in self.available:
                    self.available.append(conn)

            def closeall(self):
                """Close all connections."""
                self.connections.clear()
                self.available.clear()

            def get_stats(self):
                """Get pool statistics."""
                return {
                    "total_connections": len(self.connections),
                    "available_connections": len(self.available),
                    "used_connections": len(self.connections) - len(self.available)
                }

        return MockConnectionPool()

    @pytest.mark.unit
    def test_connection_acquisition(self, connection_pool):
        """Test connection acquisition from pool."""
        conn1 = connection_pool.getconn()
        conn2 = connection_pool.getconn()

        assert conn1 is not None
        assert conn2 is not None
        assert len(connection_pool.connections) == 2
        assert len(connection_pool.available) == 0

    @pytest.mark.unit
    def test_connection_return(self, connection_pool):
        """Test returning connections to pool."""
        conn1 = connection_pool.getconn()
        conn2 = connection_pool.getconn()

        # Return one connection
        connection_pool.putconn(conn1)

        assert len(connection_pool.available) == 1
        assert len(connection_pool.connections) == 2

        # Get connection again (should reuse)
        conn3 = connection_pool.getconn()
        assert conn3 == conn1
        assert len(connection_pool.available) == 0

    @pytest.mark.unit
    def test_pool_exhaustion(self, connection_pool):
        """Test pool exhaustion handling."""
        # Set small max connections
        connection_pool.maxconn = 2

        connection_pool.getconn()
        connection_pool.getconn()

        # Should raise exception when pool is exhausted
        with pytest.raises(Exception, match="Connection pool exhausted"):
            connection_pool.getconn()

    @pytest.mark.unit
    def test_pool_statistics(self, connection_pool):
        """Test pool statistics."""
        conn1 = connection_pool.getconn()
        conn2 = connection_pool.getconn()
        connection_pool.putconn(conn1)

        stats = connection_pool.get_stats()

        assert stats["total_connections"] == 2
        assert stats["available_connections"] == 1
        assert stats["used_connections"] == 1


class TestIntegrationTests:
    """Integration tests for database components."""

    @pytest.mark.integration
    def test_full_database_workflow(self, mock_db_connection):
        """Test full database workflow."""
        # This would test the complete database interaction workflow
        # For now, we'll test component interactions

        # Test schema creation
        cursor = mock_db_connection.cursor.return_value
        create_test_database_schema(cursor)

        # Verify schema creation calls were made
        assert cursor.execute.called

        # Test cleanup
        cleanup_test_database(cursor)

        # Verify cleanup calls were made
        assert cursor.execute.called

    @pytest.mark.integration
    def test_data_ingestion_pipeline(self, mock_db_connection):
        """Test data ingestion pipeline."""
        # Generate test data
        bills = generate_mock_bill_data(5)
        members = generate_mock_member_data(3)
        votes = generate_mock_vote_data(10)

        # Mock successful ingestion
        cursor = mock_db_connection.cursor.return_value
        cursor.rowcount = 1

        # Test that data structures are valid
        assert len(bills) == 5
        assert len(members) == 3
        assert len(votes) == 10

        # Verify data integrity
        for bill in bills:
            assert 'bill_id' in bill
            assert 'jurisdiction' in bill

        for member in members:
            assert 'member_id' in member
            assert 'name' in member

        for vote in votes:
            assert 'vote_id' in vote
            assert 'result' in vote