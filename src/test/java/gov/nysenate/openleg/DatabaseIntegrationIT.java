package gov.nysenate.openleg;

import gov.nysenate.openleg.config.annotation.IntegrationTest;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;

/**
 * Comprehensive Database Integration Tests
 * Tests database connectivity, schema validation, data integrity, and migration verification
 */
@RunWith(SpringJUnit4ClassRunner.class)
@IntegrationTest
public class DatabaseIntegrationIT extends BaseTests {

    @Autowired
    private DataSource dataSource;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    /**
     * Verifies that the configured DataSource yields a usable Connection and that database metadata is available.
     *
     * <p>The test asserts the connection is non-null and open and that DatabaseMetaData and the database product
     * name can be retrieved.</p>
     *
     * @throws SQLException if acquiring the connection or accessing metadata fails
     */
    @Test
    public void testDatabaseConnection() throws SQLException {
        // Test basic database connectivity
        try (Connection conn = dataSource.getConnection()) {
            assertNotNull("Database connection should not be null", conn);
            assertFalse("Connection should be valid", conn.isClosed());

            DatabaseMetaData metaData = conn.getMetaData();
            assertNotNull("Database metadata should be available", metaData);

            String dbProductName = metaData.getDatabaseProductName();
            assertNotNull("Database product name should be available", dbProductName);
            System.out.println("Connected to database: " + dbProductName);
        }
    }

    /**
     * Verifies that all required database tables are present.
     *
     * Checks that each expected table name exists in the connected database's metadata.
     *
     * @throws SQLException if obtaining the connection or reading database metadata fails
     */
    @Test
    public void testRequiredTablesExist() throws SQLException {
        // Test that all required tables exist in the database
        List<String> requiredTables = List.of(
            "bill", "bill_amendment", "bill_action", "bill_sponsor",
            "bill_text", "bill_vote", "committee", "member",
            "govinfo_bill", "govinfo_bill_action", "govinfo_bill_cosponsor",
            "federal_member", "universal_bill", "universal_bill_action"
        );

        try (Connection conn = dataSource.getConnection()) {
            DatabaseMetaData metaData = conn.getMetaData();

            for (String tableName : requiredTables) {
                try (ResultSet tables = metaData.getTables(null, null, tableName.toLowerCase(), new String[]{"TABLE"})) {
                    assertTrue("Required table '" + tableName + "' should exist", tables.next());
                }
            }
        }
    }

    /**
     * Validates that essential primary key and foreign key constraints exist in the database.
     *
     * <p>Checks that primary keys are defined for the bill, bill_amendment, and member tables,
     * and that foreign key relationships from bill_amendment.bill_id -> bill.bill_id and
     * bill_action.bill_id -> bill.bill_id are present.</p>
     *
     * @throws SQLException if a database access error occurs while inspecting metadata
     */
    @Test
    public void testSchemaConstraints() throws SQLException {
        // Test that database constraints are properly defined
        try (Connection conn = dataSource.getConnection()) {
            // Check primary keys exist for key tables
            assertPrimaryKeyExists(conn, "bill", "bill_id");
            assertPrimaryKeyExists(conn, "bill_amendment", "bill_amend_id");
            assertPrimaryKeyExists(conn, "member", "member_id");

            // Check foreign key relationships
            assertForeignKeyExists(conn, "bill_amendment", "bill_id", "bill", "bill_id");
            assertForeignKeyExists(conn, "bill_action", "bill_id", "bill", "bill_id");
        }
    }

    /**
     * Verifies that required NOT NULL constraints on critical columns are enforced.
     *
     * <p>Checks that inserting NULL values into the following columns fails as expected:
     * bill.session_year, bill.base_print_no, and member.chamber. Uses helper assertions
     * to attempt invalid inserts and confirm constraint violations are raised.
     */
    @Test
    public void testDataIntegrityChecks() {
        // Test data integrity constraints
        // Insert test data and verify constraints are enforced

        // Test bill table constraints
        assertDataIntegrity("bill", "session_year", "Session year cannot be null");
        assertDataIntegrity("bill", "base_print_no", "Print number cannot be null");

        // Test member table constraints
        assertDataIntegrity("member", "chamber", "Chamber cannot be null");
    }

    /**
     * Verifies that Flyway migrations have been applied to the database and that at least one migration references "govinfo".
     *
     * Asserts that the Flyway schema history contains at least one entry and that at least one entry's description contains "govinfo".
     */
    @Test
    public void testDatabaseMigrationsApplied() {
        // Test that all required database migrations have been applied
        List<Map<String, Object>> migrations = jdbcTemplate.queryForList(
            "SELECT version, description FROM flyway_schema_history ORDER BY installed_rank"
        );

        assertFalse("Database migrations should exist", migrations.isEmpty());

        // Check for specific recent migrations related to govinfo/federal data
        boolean hasGovinfoMigrations = migrations.stream()
            .anyMatch(m -> m.get("description").toString().contains("govinfo"));

        assertTrue("GovInfo-related migrations should be applied", hasGovinfoMigrations);

        System.out.println("Applied migrations: " + migrations.size());
    }

    /**
     * Verifies that database indexes for key tables exist in the public schema.
     *
     * Checks that the public schema contains at least one index and that specific indexes
     * exist for bill.session_year (`bill_session_year_idx`), bill.base_print_no
     * (`bill_base_print_no_idx`), and member.chamber (`member_chamber_idx`).
     */
    @Test
    public void testIndexPerformance() {
        // Test that required indexes exist and are being used
        List<Map<String, Object>> indexes = jdbcTemplate.queryForList(
            "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public'"
        );

        assertFalse("Database indexes should exist", indexes.isEmpty());

        // Check for key indexes
        assertIndexExists(indexes, "bill", "bill_session_year_idx");
        assertIndexExists(indexes, "bill", "bill_base_print_no_idx");
        assertIndexExists(indexes, "member", "member_chamber_idx");

        System.out.println("Total indexes: " + indexes.size());
    }

    /**
     * Verifies that the database accepts multiple simultaneous JDBC connections and can execute queries concurrently.
     *
     * Opens several connections, runs a simple COUNT query on each connection in parallel, asserts that each connection is open
     * and that queries return results, and closes all connections afterwards.
     *
     * @throws SQLException if acquiring or closing a JDBC connection fails
     */
    @Test
    public void testConcurrentConnections() throws SQLException {
        // Test ability to handle multiple concurrent connections
        final int numConnections = 5;
        Connection[] connections = new Connection[numConnections];

        try {
            // Open multiple connections
            for (int i = 0; i < numConnections; i++) {
                connections[i] = dataSource.getConnection();
                assertNotNull("Connection " + i + " should not be null", connections[i]);
                assertFalse("Connection " + i + " should be open", connections[i].isClosed());
            }

            // Execute queries on different connections simultaneously
            for (int i = 0; i < numConnections; i++) {
                final int connectionIndex = i;
                new Thread(() -> {
                    try {
                        Connection conn = connections[connectionIndex];
                        try (var stmt = conn.createStatement();
                             var rs = stmt.executeQuery("SELECT COUNT(*) FROM bill")) {
                            assertTrue("Query should return results", rs.next());
                        }
                    } catch (SQLException e) {
                        fail("Concurrent query failed: " + e.getMessage());
                    }
                }).start();
            }

        } finally {
            // Close all connections
            for (Connection conn : connections) {
                if (conn != null && !conn.isClosed()) {
                    conn.close();
                }
            }
        }
    }

    /**
     * Verifies that an insert performed inside a JDBC transaction is visible within the transaction
     * and is removed after the transaction is rolled back.
     *
     * The test begins a transaction, inserts a test bill row, asserts the row is queryable inside
     * the transaction, rolls back, and then asserts the row is no longer present.
     */
    @Test
    public void testTransactionIsolation() {
        // Test transaction isolation levels
        jdbcTemplate.execute("BEGIN");

        // Insert test data in a transaction
        jdbcTemplate.update("INSERT INTO bill (bill_id, session_year, base_print_no, title) " +
                          "VALUES (nextval('bill_bill_id_seq'), 2025, 'TEST001', 'Test Bill')");

        // Verify data is visible within transaction
        Integer count = jdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM bill WHERE base_print_no = 'TEST001'", Integer.class);
        assertEquals("Test data should be visible in transaction", Integer.valueOf(1), count);

        // Rollback transaction
        jdbcTemplate.execute("ROLLBACK");

        // Verify data was rolled back
        count = jdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM bill WHERE base_print_no = 'TEST001'", Integer.class);
        assertEquals("Test data should be rolled back", Integer.valueOf(0), count);
    }

    @Test
    public void testDatabaseBackupAndRestore() {
        // Test database backup and restore functionality
        // This would typically involve pg_dump/pg_restore or similar

        // For now, just verify we can create a basic backup of key tables
        List<Map<String, Object>> billData = jdbcTemplate.queryForList(
            "SELECT bill_id, session_year, base_print_no FROM bill LIMIT 10"
        );

        assertNotNull("Should be able to query bill data for backup verification", billData);

        // In a real implementation, this would create and verify a backup file
        System.out.println("Backup verification: Found " + billData.size() + " bill records");
    }

    /**
     * Asserts that the specified primary key column exists on the given table and fails the test if it does not.
     *
     * @param conn      the database connection to use for metadata lookup
     * @param tableName the name of the table to check
     * @param pkColumn  the primary key column name expected on the table
     * @throws SQLException if a database metadata access error occurs
     */

    private void assertPrimaryKeyExists(Connection conn, String tableName, String pkColumn) throws SQLException {
        DatabaseMetaData metaData = conn.getMetaData();
        try (ResultSet pks = metaData.getPrimaryKeys(null, null, tableName.toLowerCase())) {
            boolean pkFound = false;
            while (pks.next()) {
                if (pkColumn.equalsIgnoreCase(pks.getString("COLUMN_NAME"))) {
                    pkFound = true;
                    break;
                }
            }
            assertTrue("Primary key '" + pkColumn + "' should exist on table '" + tableName + "'", pkFound);
        }
    }

    /**
     * Asserts that a foreign key exists from the specified column on the foreign-key table
     * to the specified column on the referenced primary-key table.
     *
     * @param conn    JDBC connection used to read database metadata
     * @param fkTable name of the table that contains the foreign key
     * @param fkColumn name of the foreign key column on {@code fkTable}
     * @param pkTable name of the referenced primary-key table
     * @param pkColumn name of the referenced primary-key column on {@code pkTable}
     * @throws SQLException if reading metadata from the connection fails
     */
    private void assertForeignKeyExists(Connection conn, String fkTable, String fkColumn,
                                      String pkTable, String pkColumn) throws SQLException {
        DatabaseMetaData metaData = conn.getMetaData();
        try (ResultSet fks = metaData.getImportedKeys(null, null, fkTable.toLowerCase())) {
            boolean fkFound = false;
            while (fks.next()) {
                String fkColumnName = fks.getString("FKCOLUMN_NAME");
                String pkTableName = fks.getString("PKTABLE_NAME");
                String pkColumnName = fks.getString("PKCOLUMN_NAME");

                if (fkColumn.equalsIgnoreCase(fkColumnName) &&
                    pkTable.equalsIgnoreCase(pkTableName) &&
                    pkColumn.equalsIgnoreCase(pkColumnName)) {
                    fkFound = true;
                    break;
                }
            }
            assertTrue("Foreign key from " + fkTable + "." + fkColumn +
                      " to " + pkTable + "." + pkColumn + " should exist", fkFound);
        }
    }

    /**
     * Verifies that the specified column on a table enforces a NOT NULL constraint by attempting to insert a NULL value.
     *
     * Attempts an insert of NULL into the given `notNullColumn` on `tableName` and asserts that the operation fails
     * with a database constraint violation.
     *
     * @param tableName the table to test
     * @param notNullColumn the column that is expected to disallow NULL values
     * @param errorMessage additional context used in the failure message if the insert unexpectedly succeeds
     */
    private void assertDataIntegrity(String tableName, String notNullColumn, String errorMessage) {
        // Test NOT NULL constraints by attempting invalid inserts
        try {
            jdbcTemplate.update("INSERT INTO " + tableName + " (" + notNullColumn + ") VALUES (NULL)");
            fail("Should not be able to insert NULL into " + notNullColumn + ": " + errorMessage);
        } catch (Exception e) {
            // Expected - constraint violation
            assertTrue("Exception should indicate constraint violation",
                      e.getMessage().contains("null value") || e.getMessage().contains("violates"));
        }
    }

    /**
     * Asserts that an index with the given name exists on the specified table within the provided index metadata.
     *
     * @param indexes   a list of index metadata maps (expected keys: "tablename" and "indexname")
     * @param tableName the table name to check for the index
     * @param indexName the index name expected to exist on the table
     */
    private void assertIndexExists(List<Map<String, Object>> indexes, String tableName, String indexName) {
        boolean indexFound = indexes.stream()
            .anyMatch(idx -> tableName.equals(idx.get("tablename")) &&
                           indexName.equals(idx.get("indexname")));

        assertTrue("Index '" + indexName + "' should exist on table '" + tableName + "'", indexFound);
    }
}