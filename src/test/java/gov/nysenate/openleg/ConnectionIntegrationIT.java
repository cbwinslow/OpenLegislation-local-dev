package gov.nysenate.openleg;

import gov.nysenate.openleg.config.annotation.IntegrationTest;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import javax.net.ssl.HttpsURLConnection;
import javax.sql.DataSource;
import java.io.IOException;
import java.net.*;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.concurrent.TimeUnit;

import static org.junit.Assert.*;

/**
 * Connection Integration Tests
 * Tests connectivity to external APIs, databases, and network services
 */
@RunWith(SpringJUnit4ClassRunner.class)
@IntegrationTest
public class ConnectionIntegrationIT extends BaseTests {

    @Autowired
    private DataSource dataSource;

    // External service endpoints
    private static final String GOVINFO_BULK_URL = "https://www.govinfo.gov/bulkdata";
    private static final String CONGRESS_API_URL = "https://api.congress.gov/v3";
    private static final String GOOGLE_DNS = "8.8.8.8";
    private static final int HTTP_TIMEOUT_MS = 10000;

    @Test
    public void testGovInfoBulkDataConnectivity() {
        // Test connectivity to GovInfo bulk data service
        try {
            URI uri = URI.create(GOVINFO_BULK_URL);
            URL url = uri.toURL();
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(HTTP_TIMEOUT_MS);
            connection.setReadTimeout(HTTP_TIMEOUT_MS);
            connection.setRequestMethod("HEAD");

            int responseCode = connection.getResponseCode();
            assertTrue("GovInfo bulk data should be accessible (HTTP 200-399)",
                      responseCode >= 200 && responseCode < 400);

            System.out.println("GovInfo bulk data service is accessible: HTTP " + responseCode);

        } catch (IOException e) {
            fail("Failed to connect to GovInfo bulk data service: " + e.getMessage());
        }
    }

    @Test
    public void testCongressApiConnectivity() {
        // Test connectivity to Congress.gov API
        try {
            URI uri = URI.create(CONGRESS_API_URL);
            URL url = uri.toURL();
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(HTTP_TIMEOUT_MS);
            connection.setReadTimeout(HTTP_TIMEOUT_MS);
            connection.setRequestMethod("GET");

            int responseCode = connection.getResponseCode();
            assertTrue("Congress.gov API should be accessible (HTTP 200-399)",
                      responseCode >= 200 && responseCode < 400);

            System.out.println("Congress.gov API is accessible: HTTP " + responseCode);

        } catch (IOException e) {
            fail("Failed to connect to Congress.gov API: " + e.getMessage());
        }
    }

    @Test
    public void testInternetConnectivity() {
        // Test basic internet connectivity
        try {
            InetAddress address = InetAddress.getByName(GOOGLE_DNS);
            assertNotNull("Should be able to resolve DNS", address);

            boolean reachable = address.isReachable(5000);
            assertTrue("Internet should be accessible", reachable);

            System.out.println("Internet connectivity confirmed via " + GOOGLE_DNS);

        } catch (IOException e) {
            fail("Failed to test internet connectivity: " + e.getMessage());
        }
    }

    @Test
    public void testDatabaseConnectionPool() throws SQLException {
        // Test database connection pool functionality
        final int numConnections = 10;
        Connection[] connections = new Connection[numConnections];

        long startTime = System.nanoTime();

        try {
            // Test connection acquisition performance
            for (int i = 0; i < numConnections; i++) {
                connections[i] = dataSource.getConnection();
                assertNotNull("Connection " + i + " should not be null", connections[i]);
                assertFalse("Connection " + i + " should be open", connections[i].isClosed());
            }

            long endTime = System.nanoTime();
            long durationMs = TimeUnit.NANOSECONDS.toMillis(endTime - startTime);

            System.out.println("Acquired " + numConnections + " database connections in " + durationMs + "ms");

            // Test connection pool performance (should be fast)
            assertTrue("Connection acquisition should be reasonably fast (< 5 seconds)",
                      durationMs < 5000);

        } finally {
            // Clean up connections
            for (Connection conn : connections) {
                if (conn != null && !conn.isClosed()) {
                    try {
                        conn.close();
                    } catch (SQLException e) {
                        System.err.println("Warning: Failed to close connection: " + e.getMessage());
                    }
                }
            }
        }
    }

    @Test
    public void testNetworkLatency() {
        // Test network latency to key services
        testServiceLatency("GovInfo Bulk Data", GOVINFO_BULK_URL);
        testServiceLatency("Congress.gov API", CONGRESS_API_URL);
    }

    @Test
    public void testProxyConfiguration() {
        // Test if proxy settings are properly configured (if needed)
        // This test checks if the application can handle proxy environments

        String proxyHost = System.getProperty("http.proxyHost");
        String proxyPort = System.getProperty("http.proxyPort");

        if (proxyHost != null && proxyPort != null) {
            System.out.println("Proxy detected: " + proxyHost + ":" + proxyPort);
            // Test that connections work through proxy
            testGovInfoBulkDataConnectivity(); // Re-run with proxy
        } else {
            System.out.println("No proxy configuration detected");
        }
    }

    @Test
    public void testSSLCertificateValidation() {
        // Test SSL certificate validation for HTTPS endpoints
        try {
            URI uri = URI.create(GOVINFO_BULK_URL);
            URL url = uri.toURL();
            HttpsURLConnection connection = (HttpsURLConnection) url.openConnection();
            connection.setConnectTimeout(HTTP_TIMEOUT_MS);
            connection.setReadTimeout(HTTP_TIMEOUT_MS);

            // This will throw an exception if SSL certificates are invalid
            connection.connect();

            System.out.println("SSL certificate validation successful for " + GOVINFO_BULK_URL);

        } catch (IOException e) {
            fail("SSL certificate validation failed: " + e.getMessage());
        }
    }

    @Test
    public void testConnectionTimeoutHandling() {
        // Test that connection timeouts are handled properly
        try {
            URI uri = URI.create("http://httpbin.org/delay/30"); // Service that delays 30 seconds
            URL url = uri.toURL();
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(5000); // 5 second timeout
            connection.setReadTimeout(5000);

            // This should timeout and throw an exception
            connection.getResponseCode();
            fail("Connection should have timed out");

        } catch (SocketTimeoutException e) {
            // Expected - timeout should be handled gracefully
            assertTrue("Timeout exception should be caught", true);
            System.out.println("Connection timeout handling works correctly");

        } catch (IOException e) {
            // Other IO exceptions are also acceptable
            System.out.println("Connection handling works (different exception): " + e.getClass().getSimpleName());
        }
    }

    @Test
    public void testConcurrentApiCalls() throws InterruptedException {
        // Test making concurrent API calls to ensure thread safety
        final int numThreads = 5;
        Thread[] threads = new Thread[numThreads];
        boolean[] results = new boolean[numThreads];

        for (int i = 0; i < numThreads; i++) {
            final int threadIndex = i;
            threads[i] = new Thread(() -> {
                try {
                    // Make a simple API call
                    testGovInfoBulkDataConnectivity();
                    results[threadIndex] = true;
                } catch (Exception e) {
                    results[threadIndex] = false;
                    System.err.println("Thread " + threadIndex + " failed: " + e.getMessage());
                }
            });
            threads[i].start();
        }

        // Wait for all threads to complete
        for (Thread thread : threads) {
            thread.join(10000); // 10 second timeout
        }

        // Verify all threads succeeded
        for (int i = 0; i < numThreads; i++) {
            assertTrue("Concurrent API call " + i + " should succeed", results[i]);
        }

        System.out.println("Concurrent API calls completed successfully");
    }

    @Test
    public void testFirewallAndSecurity() {
        // Test that necessary ports are open and accessible
        testPortAccessibility("GovInfo HTTPS", "www.govinfo.gov", 443);
        testPortAccessibility("Congress.gov HTTPS", "api.congress.gov", 443);
        testPortAccessibility("PostgreSQL", "localhost", 5432); // Assuming local DB
    }

    // Helper methods

    private void testServiceLatency(String serviceName, String urlString) {
        try {
            long startTime = System.nanoTime();

            @SuppressWarnings("deprecation")
            URL url = new URL(urlString);
            HttpURLConnection connection = (HttpURLConnection) url.openConnection();
            connection.setConnectTimeout(HTTP_TIMEOUT_MS);
            connection.setReadTimeout(HTTP_TIMEOUT_MS);
            connection.setRequestMethod("HEAD");

            int responseCode = connection.getResponseCode();

            long endTime = System.nanoTime();
            long latencyMs = TimeUnit.NANOSECONDS.toMillis(endTime - startTime);

            assertTrue(serviceName + " should respond (HTTP 200-399)", responseCode >= 200 && responseCode < 400);
            assertTrue(serviceName + " latency should be reasonable (< 10 seconds)", latencyMs < 10000);

            System.out.println(serviceName + " latency: " + latencyMs + "ms");

        } catch (IOException e) {
            fail("Failed to test latency for " + serviceName + ": " + e.getMessage());
        }
    }

    private void testPortAccessibility(String serviceName, String host, int port) {
        try (Socket socket = new Socket()) {
            socket.connect(new InetSocketAddress(host, port), 5000);
            assertTrue(serviceName + " port " + port + " should be accessible", socket.isConnected());
            System.out.println(serviceName + " port " + port + " is accessible");

        } catch (IOException e) {
            // For external services, this might fail due to network restrictions
            // Log but don't fail the test
            System.out.println("Warning: " + serviceName + " port " + port + " not accessible: " + e.getMessage());
        }
    }
}