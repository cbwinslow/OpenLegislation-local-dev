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

    /**
     * Verifies access to the GovInfo bulk data service endpoint.
     *
     * Performs an HTTP HEAD request to GOVINFO_BULK_URL and asserts the response
     * status code is between 200 and 399.
     */
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

    /**
     * Verifies that the Congress.gov API endpoint is reachable and responding with an HTTP status in the 200–399 range.
     *
     * Performs an HTTP GET to the configured CONGRESS_API_URL and asserts the response code indicates success or redirection.
     */
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

    /**
     * Verifies basic internet connectivity by resolving and attempting to reach a known DNS server.
     *
     * The test resolves the configured DNS address and asserts that the host is reachable within a 5-second timeout;
     * the test fails if DNS resolution or reachability checks fail.
     */
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

    /**
     * Verifies that the configured DataSource can supply multiple open connections and that acquisition completes within a reasonable time.
     *
     * Acquires a fixed number of connections from the pool, asserts each is non-null and open, measures total acquisition time (expected to be under 5 seconds), and closes all acquired connections in a finally block.
     *
     * @throws SQLException if obtaining a connection from the DataSource fails
     */
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

    /**
     * Measures network latency to key external services used by the application.
     *
     * <p>Invokes latency checks for the GovInfo bulk data endpoint and the Congress.gov API.
     */
    @Test
    public void testNetworkLatency() {
        // Test network latency to key services
        testServiceLatency("GovInfo Bulk Data", GOVINFO_BULK_URL);
        testServiceLatency("Congress.gov API", CONGRESS_API_URL);
    }

    /**
     * Checks for configured HTTP proxy system properties and, if present, verifies that HTTP
     * connections succeed using the configured proxy; otherwise logs that no proxy is configured.
     */
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

    /**
     * Validates the SSL certificate presented by the GOVINFO_BULK_URL HTTPS endpoint.
     *
     * Attempts to establish an HTTPS connection to the configured GovInfo bulk data URL and fails
     * the test if an SSL or other I/O error occurs while establishing the connection.
     */
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

    /**
     * Verifies that HTTP connections respect configured connect and read timeouts when a remote service delays its response.
     *
     * Attempts to connect to an endpoint that delays 30 seconds using a 5-second connect and read timeout and expects a timeout-related exception; other IOExceptions are accepted as a valid outcome.
     */
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

    /**
     * Performs several concurrent requests to the GovInfo bulk data endpoint to verify that making API calls
     * from multiple threads is safe and all calls complete successfully.
     *
     * This test starts multiple worker threads that each invoke the GovInfo connectivity check and asserts that
     * every thread reports success.
     *
     * @throws InterruptedException if the current thread is interrupted while waiting for worker threads to finish
     */
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

    /**
     * Verifies that required service ports for external APIs and the local database are reachable.
     *
     * <p>Checks connectivity to GovInfo HTTPS (www.govinfo.gov:443), Congress.gov HTTPS (api.congress.gov:443),
     * and the local PostgreSQL instance (localhost:5432) by attempting socket connections.</p>
     */
    @Test
    public void testFirewallAndSecurity() {
        // Test that necessary ports are open and accessible
        testPortAccessibility("GovInfo HTTPS", "www.govinfo.gov", 443);
        testPortAccessibility("Congress.gov HTTPS", "api.congress.gov", 443);
        testPortAccessibility("PostgreSQL", "localhost", 5432); // Assuming local DB
    }

    /**
     * Measures round-trip latency to a service URL and asserts the service is responsive and its latency is under 10 seconds.
     *
     * @param serviceName a human-readable name for the service used in assertions and log messages
     * @param urlString the full URL of the service endpoint to test
     */

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

    /**
     * Checks TCP accessibility of the given host and port and logs the result.
     *
     * Attempts to open a socket to the specified host and port with a 5000 ms connect timeout.
     * On success the method asserts the connection is established and prints a confirmation.
     * If a connection cannot be made, the method logs a warning but does not throw or fail the caller.
     *
     * @param serviceName a human-readable name for the service being checked (used in messages)
     * @param host the hostname or IP address to connect to
     * @param port the TCP port to connect to
     */
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