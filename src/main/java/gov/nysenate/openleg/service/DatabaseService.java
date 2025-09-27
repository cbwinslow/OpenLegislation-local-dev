package gov.nysenate.openleg.service;

import org.flywaydb.core.Flyway;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import javax.sql.DataSource;

@Service
public class DatabaseService {

    private static final Logger logger = LoggerFactory.getLogger(DatabaseService.class);

    private final DataSource dataSource;

    public DatabaseService(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    /**
     * Programmatically runs the Flyway database migrations.
     */
    public void migrateDatabase() {
        logger.info("Starting database migration...");
        try {
            Flyway flyway = Flyway.configure()
                    .dataSource(dataSource)
                    .locations("classpath:db/migration") // Flyway's default, but explicit is better
                    .load();

            flyway.migrate();
            logger.info("Database migration completed successfully.");
        } catch (Exception e) {
            logger.error("Database migration failed.", e);
            // In a real application, you might want to re-throw this as a custom exception.
        }
    }
}