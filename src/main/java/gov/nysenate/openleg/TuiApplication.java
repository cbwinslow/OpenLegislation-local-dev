package gov.nysenate.openleg;

import com.googlecode.lanterna.terminal.DefaultTerminalFactory;
import com.googlecode.lanterna.gui2.dialogs.TextInputDialog;
import com.googlecode.lanterna.terminal.DefaultTerminalFactory;
import com.googlecode.lanterna.terminal.Terminal;
import gov.nysenate.openleg.ingestion.GovinfoApiIngester;
import gov.nysenate.openleg.ingestion.GovinfoBulkIngester;
import gov.nysenate.openleg.service.DatabaseService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.orm.jpa.JpaTransactionManager;
import org.springframework.orm.jpa.LocalContainerEntityManagerFactoryBean;
import org.springframework.orm.jpa.vendor.HibernateJpaVendorAdapter;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.annotation.EnableTransactionManagement;

import javax.sql.DataSource;
import java.io.IOException;
import java.util.Properties;

@Configuration
@EnableJpaRepositories(basePackages = "gov.nysenate.openleg.db.repository")
@EnableTransactionManagement
@ComponentScan(basePackages = "gov.nysenate.openleg")
public class TuiApplication {

    private static final Logger logger = LoggerFactory.getLogger(TuiApplication.class);

    public static void main(String[] args) {
        logger.info("Initializing Spring context for TUI application...");
        try (AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(TuiApplication.class)) {
            logger.info("Spring context initialized.");

            // Get services from context
            DatabaseService databaseService = context.getBean(DatabaseService.class);
            GovinfoBulkIngester bulkIngester = context.getBean(GovinfoBulkIngester.class);
            GovinfoApiIngester apiIngester = context.getBean(GovinfoApiIngester.class);

            DefaultTerminalFactory defaultTerminalFactory = new DefaultTerminalFactory();
            try (Terminal terminal = defaultTerminalFactory.createTerminal()) {
                // TUI setup
                com.googlecode.lanterna.screen.Screen screen = new com.googlecode.lanterna.screen.TerminalScreen(terminal);
                screen.startScreen();

                com.googlecode.lanterna.gui2.WindowBasedTextGUI gui = new com.googlecode.lanterna.gui2.MultiWindowTextGUI(screen);
                com.googlecode.lanterna.gui2.BasicWindow window = new com.googlecode.lanterna.gui2.BasicWindow("OpenLegislation TUI");

                com.googlecode.lanterna.gui2.Panel contentPanel = new com.googlecode.lanterna.gui2.Panel(new com.googlecode.lanterna.graphics.SimpleTheme());
                contentPanel.setLayoutManager(new com.googlecode.lanterna.gui2.LinearLayout(com.googlecode.lanterna.gui2.Direction.VERTICAL));

                contentPanel.addComponent(new com.googlecode.lanterna.gui2.Label("Select an action:"));

                com.googlecode.lanterna.gui2.ActionListBox actionListBox = new com.googlecode.lanterna.gui2.ActionListBox();
                actionListBox.addItem("Deploy/Migrate Database", () -> {
                    try {
                        databaseService.migrateDatabase();
                        com.googlecode.lanterna.gui2.dialogs.MessageDialog.showMessageDialog(gui, "Success", "Database migration completed successfully.");
                    } catch (Exception e) {
                        logger.error("Database migration failed from TUI.", e);
                        com.googlecode.lanterna.gui2.dialogs.MessageDialog.showMessageDialog(gui, "Error", "Database migration failed:\n" + e.getMessage());
                    }
                });
                actionListBox.addItem("Run Bulk Data Ingestion", () -> {
                    try {
                        String congressStr = TextInputDialog.showDialog(gui, "Bulk Ingestion", "Enter Congress Number:", "");
                        if (congressStr != null && !congressStr.isEmpty()) {
                            int congress = Integer.parseInt(congressStr);
                            bulkIngester.ingest(congress);
                            com.googlecode.lanterna.gui2.dialogs.MessageDialog.showMessageDialog(gui, "Success", "Bulk ingestion for congress " + congress + " completed.");
                        }
                    } catch (Exception e) {
                        logger.error("Bulk ingestion failed from TUI.", e);
                        com.googlecode.lanterna.gui2.dialogs.MessageDialog.showMessageDialog(gui, "Error", "Bulk ingestion failed:\n" + e.getMessage());
                    }
                });
                actionListBox.addItem("Run API Data Ingestion", () -> {
                    try {
                        String packageId = TextInputDialog.showDialog(gui, "API Ingestion", "Enter Package ID:", "");
                        if (packageId != null && !packageId.isEmpty()) {
                            apiIngester.ingest(packageId);
                            com.googlecode.lanterna.gui2.dialogs.MessageDialog.showMessageDialog(gui, "Success", "API ingestion for package " + packageId + " completed.");
                        }
                    } catch (Exception e) {
                        logger.error("API ingestion failed from TUI.", e);
                        com.googlecode.lanterna.gui2.dialogs.MessageDialog.showMessageDialog(gui, "Error", "API ingestion failed:\n" + e.getMessage());
                    }
                });
                actionListBox.addItem("Exit", window::close);

                contentPanel.addComponent(actionListBox);
                window.setComponent(contentPanel);

                gui.addWindowAndWait(window);

            } catch (IOException e) {
                logger.error("An error occurred with the terminal.", e);
            }
        } catch (Exception e) {
            logger.error("An error occurred during application startup.", e);
        }
    }

    @javax.annotation.Bean
    public DataSource dataSource() {
        DriverManagerDataSource dataSource = new DriverManagerDataSource();
        dataSource.setDriverClassName("org.postgresql.Driver");
        dataSource.setUrl(System.getenv("DB_URL"));
        dataSource.setUsername(System.getenv("DB_USERNAME"));
        dataSource.setPassword(System.getenv("DB_PASSWORD"));
        return dataSource;
    }

    @javax.annotation.Bean
    public LocalContainerEntityManagerFactoryBean entityManagerFactory() {
        LocalContainerEntityManagerFactoryBean em = new LocalContainerEntityManagerFactoryBean();
        em.setDataSource(dataSource());
        em.setPackagesToScan("gov.nysenate.openleg.model.db");

        HibernateJpaVendorAdapter vendorAdapter = new HibernateJpaVendorAdapter();
        em.setJpaVendorAdapter(vendorAdapter);

        Properties properties = new Properties();
        properties.setProperty("hibernate.hbm2ddl.auto", "validate");
        properties.setProperty("hibernate.dialect", "org.hibernate.dialect.PostgreSQLDialect");
        em.setJpaProperties(properties);

        return em;
    }

    @javax.annotation.Bean
    public PlatformTransactionManager transactionManager() {
        JpaTransactionManager transactionManager = new JpaTransactionManager();
        transactionManager.setEntityManagerFactory(entityManagerFactory().getObject());
        return transactionManager;
    }
}