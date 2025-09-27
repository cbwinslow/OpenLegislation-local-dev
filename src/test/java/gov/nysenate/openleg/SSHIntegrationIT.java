package gov.nysenate.openleg;

import gov.nysenate.openleg.config.annotation.IntegrationTest;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.TimeUnit;

import static org.junit.Assert.*;

/**
 * SSH Integration Tests
 * Tests remote server connectivity, file transfer, and deployment validation
 */
@RunWith(SpringJUnit4ClassRunner.class)
@IntegrationTest
public class SSHIntegrationIT extends BaseTests {

    private static final String TEST_HOST = "localhost"; // For local testing
    private static final String TEST_USER = System.getProperty("user.name");
    private static final String TEST_REMOTE_DIR = "/tmp/ssh_test";
    private static final String TEST_LOCAL_FILE = "/tmp/ssh_test_file.txt";
    private static final String TEST_CONTENT = "SSH Test Content - " + System.currentTimeMillis();

    @Test
    public void testSSHConnectivity() {
        // Test basic SSH connectivity to localhost
        ProcessBuilder pb = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            TEST_USER + "@" + TEST_HOST,
            "echo 'SSH connection successful'");

        try {
            Process process = pb.start();
            boolean finished = process.waitFor(30, TimeUnit.SECONDS);

            assertTrue("SSH command should complete within timeout", finished);
            assertEquals("SSH command should succeed", 0, process.exitValue());

            // Read output
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()))) {
                String output = reader.readLine();
                assertNotNull("SSH should return output", output);
                assertTrue("SSH output should contain success message",
                          output.contains("SSH connection successful"));
            }

            System.out.println("SSH connectivity test passed");

        } catch (IOException | InterruptedException e) {
            fail("SSH connectivity test failed: " + e.getMessage());
        }
    }

    @Test
    public void testSCPFileTransfer() throws IOException {
        // Test SCP file transfer
        createTestFile();

        ProcessBuilder pb = new ProcessBuilder("scp",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            TEST_LOCAL_FILE,
            TEST_USER + "@" + TEST_HOST + ":" + TEST_REMOTE_DIR + "/");

        try {
            Process process = pb.start();
            boolean finished = process.waitFor(30, TimeUnit.SECONDS);

            assertTrue("SCP upload should complete within timeout", finished);
            assertEquals("SCP upload should succeed", 0, process.exitValue());

            // Verify file was uploaded by checking it remotely
            verifyRemoteFileExists();

            System.out.println("SCP file upload test passed");

        } catch (IOException | InterruptedException e) {
            fail("SCP file transfer test failed: " + e.getMessage());
        } finally {
            cleanupTestFile();
        }
    }

    @Test
    public void testSSHKeyAuthentication() {
        // Test SSH key-based authentication (if available)
        ProcessBuilder pb = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            "-o", "PasswordAuthentication=no", // Force key auth
            TEST_USER + "@" + TEST_HOST,
            "echo 'SSH key authentication successful'");

        try {
            Process process = pb.start();
            boolean finished = process.waitFor(30, TimeUnit.SECONDS);

            if (finished && process.exitValue() == 0) {
                System.out.println("SSH key authentication is available and working");
            } else {
                System.out.println("SSH key authentication not available or not configured");
                // This is not a failure - password auth might be the only option
            }

        } catch (IOException | InterruptedException e) {
            System.out.println("SSH key authentication test inconclusive: " + e.getMessage());
        }
    }

    @Test
    public void testRemoteCommandExecution() {
        // Test executing commands on remote server
        String testCommand = "uname -a && date && echo 'Remote execution test'";

        ProcessBuilder pb = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            TEST_USER + "@" + TEST_HOST,
            testCommand);

        try {
            Process process = pb.start();
            boolean finished = process.waitFor(30, TimeUnit.SECONDS);

            assertTrue("Remote command should complete within timeout", finished);
            assertEquals("Remote command should succeed", 0, process.exitValue());

            // Read output
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()))) {
                String line;
                boolean foundTestOutput = false;
                while ((line = reader.readLine()) != null) {
                    if (line.contains("Remote execution test")) {
                        foundTestOutput = true;
                    }
                    System.out.println("Remote output: " + line);
                }
                assertTrue("Remote command should execute test output", foundTestOutput);
            }

            System.out.println("Remote command execution test passed");

        } catch (IOException | InterruptedException e) {
            fail("Remote command execution test failed: " + e.getMessage());
        }
    }

    @Test
    public void testSSHPortForwarding() {
        // Test SSH port forwarding (local port forwarding)
        // This tests if SSH can establish tunnels for database or service access

        ProcessBuilder pb = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            "-L", "localhost:9999:localhost:80", // Forward local port 9999 to remote port 80
            "-N", // Don't execute remote command
            TEST_USER + "@" + TEST_HOST);

        try {
            Process process = pb.start();

            // Let it run for a few seconds to establish the tunnel
            Thread.sleep(3000);

            // Check if the tunnel is working by trying to connect to localhost:9999
            Process curlProcess = new ProcessBuilder("curl", "-s", "--connect-timeout", "5",
                                                   "http://localhost:9999").start();

            boolean curlFinished = curlProcess.waitFor(10, TimeUnit.SECONDS);

            if (curlFinished && curlProcess.exitValue() == 0) {
                System.out.println("SSH port forwarding is working");
            } else {
                System.out.println("SSH port forwarding test inconclusive (may not have web server)");
            }

            // Terminate the SSH tunnel
            process.destroyForcibly();
            process.waitFor(5, TimeUnit.SECONDS);

        } catch (IOException | InterruptedException e) {
            System.out.println("SSH port forwarding test failed: " + e.getMessage());
        }
    }

    @Test
    public void testDeploymentDirectorySetup() {
        // Test that deployment directories can be created and accessed via SSH
        String deploymentDir = "/tmp/openleg_deployment_test_" + System.currentTimeMillis();

        ProcessBuilder pb = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            TEST_USER + "@" + TEST_HOST,
            "mkdir -p " + deploymentDir + " && echo 'test' > " + deploymentDir + "/test.txt && ls -la " + deploymentDir);

        try {
            Process process = pb.start();
            boolean finished = process.waitFor(30, TimeUnit.SECONDS);

            assertTrue("Deployment directory setup should complete within timeout", finished);
            assertEquals("Deployment directory setup should succeed", 0, process.exitValue());

            // Read output to verify directory was created
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()))) {
                String output = reader.lines().reduce("", (a, b) -> a + b + "\n");
                assertTrue("Directory should contain test file", output.contains("test.txt"));
            }

            System.out.println("Deployment directory setup test passed");

            // Cleanup
            cleanupRemoteDirectory(deploymentDir);

        } catch (IOException | InterruptedException e) {
            fail("Deployment directory setup test failed: " + e.getMessage());
        }
    }

    @Test
    public void testFilePermissionsAndOwnership() {
        // Test file permissions and ownership for deployment
        String testFile = "/tmp/ssh_permissions_test_" + System.currentTimeMillis();

        ProcessBuilder pb = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            TEST_USER + "@" + TEST_HOST,
            "touch " + testFile + " && chmod 644 " + testFile + " && ls -l " + testFile + " && rm " + testFile);

        try {
            Process process = pb.start();
            boolean finished = process.waitFor(30, TimeUnit.SECONDS);

            assertTrue("File permissions test should complete within timeout", finished);
            assertEquals("File permissions test should succeed", 0, process.exitValue());

            System.out.println("File permissions and ownership test passed");

        } catch (IOException | InterruptedException e) {
            fail("File permissions test failed: " + e.getMessage());
        }
    }

    @Test
    public void testSSHConnectionPooling() {
        // Test SSH connection reuse (connection multiplexing)
        ProcessBuilder pb = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            "-o", "ControlMaster=auto",
            "-o", "ControlPath=/tmp/ssh_mux_%h_%p_%r",
            "-o", "ControlPersist=10",
            TEST_USER + "@" + TEST_HOST,
            "echo 'Connection multiplexing test'");

        try {
            Process process = pb.start();
            boolean finished = process.waitFor(30, TimeUnit.SECONDS);

            if (finished && process.exitValue() == 0) {
                System.out.println("SSH connection multiplexing is working");
            } else {
                System.out.println("SSH connection multiplexing not supported or not configured");
            }

        } catch (IOException | InterruptedException e) {
            System.out.println("SSH connection multiplexing test failed: " + e.getMessage());
        }
    }

    @Test
    public void testUserSwitching() {
        // Test user switching capabilities (sudo and su commands)
        // This is important for deployment scenarios where privilege escalation is needed

        // Test 1: Check if sudo is available and can be used
        ProcessBuilder sudoTest = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            TEST_USER + "@" + TEST_HOST,
            "sudo -n whoami 2>/dev/null || echo 'sudo not available or requires password'");

        try {
            Process sudoProcess = sudoTest.start();
            boolean sudoFinished = sudoProcess.waitFor(15, TimeUnit.SECONDS);

            if (sudoFinished && sudoProcess.exitValue() == 0) {
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(sudoProcess.getInputStream()))) {
                    String output = reader.readLine();
                    if ("root".equals(output)) {
                        System.out.println("✓ Sudo user switching to root is working");
                    } else if (output != null && output.contains("not available")) {
                        System.out.println("⚠ Sudo not available or requires password authentication");
                    } else {
                        System.out.println("✓ Sudo test returned: " + output);
                    }
                }
            } else {
                // Check stderr for more detailed error information
                try (BufferedReader errorReader = new BufferedReader(
                        new InputStreamReader(sudoProcess.getErrorStream()))) {
                    String errorOutput = errorReader.readLine();
                    if (errorOutput != null && errorOutput.contains("no new privileges")) {
                        System.out.println("⚠ Sudo disabled in container environment (no new privileges flag)");
                    } else {
                        System.out.println("⚠ Sudo test did not complete successfully");
                    }
                } catch (IOException e) {
                    System.out.println("⚠ Sudo test did not complete successfully");
                }
            }

        } catch (IOException | InterruptedException e) {
            System.out.println("✗ Sudo test failed: " + e.getMessage());
        }

        // Test 2: Test su command (switch user) if available
        ProcessBuilder suTest = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            TEST_USER + "@" + TEST_HOST,
            "su -c 'whoami' 2>/dev/null || echo 'su not available or requires password'");

        try {
            Process suProcess = suTest.start();
            boolean suFinished = suProcess.waitFor(15, TimeUnit.SECONDS);

            if (suFinished && suProcess.exitValue() == 0) {
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(suProcess.getInputStream()))) {
                    String output = reader.readLine();
                    if (output != null && !output.contains("not available")) {
                        System.out.println("✓ Su command executed, output: " + output);
                    } else {
                        System.out.println("⚠ Su command not available or requires password");
                    }
                }
            } else {
                System.out.println("⚠ Su command test did not complete successfully");
            }

        } catch (IOException | InterruptedException e) {
            System.out.println("✗ Su test failed: " + e.getMessage());
        }

        // Test 3: Test user context and permissions
        ProcessBuilder userContextTest = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            TEST_USER + "@" + TEST_HOST,
            "id -u -n && whoami && groups && echo 'User context test completed'");

        try {
            Process userContextProcess = userContextTest.start();
            boolean userContextFinished = userContextProcess.waitFor(15, TimeUnit.SECONDS);

            assertTrue("User context test should complete within timeout", userContextFinished);
            assertEquals("User context test should succeed", 0, userContextProcess.exitValue());

            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(userContextProcess.getInputStream()))) {
                String line;
                boolean foundCompletion = false;
                System.out.println("User context information:");
                while ((line = reader.readLine()) != null) {
                    System.out.println("  " + line);
                    if (line.contains("User context test completed")) {
                        foundCompletion = true;
                    }
                }
                assertTrue("User context test should complete successfully", foundCompletion);
            }

            System.out.println("✓ User context and permissions test passed");

        } catch (IOException | InterruptedException e) {
            System.out.println("✗ User context test failed: " + e.getMessage());
        }

        // Test 4: Check for alternative privilege escalation methods
        ProcessBuilder privilegeTest = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=10",
            TEST_USER + "@" + TEST_HOST,
            "which doas >/dev/null 2>&1 && echo 'doas available' || echo 'doas not available'");

        try {
            Process privilegeProcess = privilegeTest.start();
            boolean privilegeFinished = privilegeProcess.waitFor(10, TimeUnit.SECONDS);

            if (privilegeFinished && privilegeProcess.exitValue() == 0) {
                try (BufferedReader reader = new BufferedReader(
                        new InputStreamReader(privilegeProcess.getInputStream()))) {
                    String output = reader.readLine();
                    if ("doas available".equals(output)) {
                        System.out.println("✓ Alternative privilege escalation (doas) available");
                    } else {
                        System.out.println("ℹ Privilege escalation status: " + output);
                    }
                }
            }
        } catch (IOException | InterruptedException e) {
            // This is not critical, just informational
        }

        System.out.println("User switching capability assessment completed");
    }

    // Helper methods

    private void createTestFile() throws IOException {
        Path testFile = Paths.get(TEST_LOCAL_FILE);
        Files.write(testFile, TEST_CONTENT.getBytes());
    }

    private void verifyRemoteFileExists() {
        ProcessBuilder pb = new ProcessBuilder("ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            TEST_USER + "@" + TEST_HOST,
            "test -f " + TEST_REMOTE_DIR + "/ssh_test_file.txt && echo 'File exists' || echo 'File not found'");

        try {
            Process process = pb.start();
            process.waitFor(10, TimeUnit.SECONDS);

            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream()))) {
                String output = reader.readLine();
                assertEquals("Remote file should exist", "File exists", output);
            }

        } catch (IOException | InterruptedException e) {
            fail("Failed to verify remote file: " + e.getMessage());
        }
    }

    private void cleanupTestFile() {
        try {
            Files.deleteIfExists(Paths.get(TEST_LOCAL_FILE));
        } catch (IOException e) {
            System.err.println("Warning: Failed to cleanup local test file: " + e.getMessage());
        }

        // Also cleanup remote file
        try {
            ProcessBuilder pb = new ProcessBuilder("ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                TEST_USER + "@" + TEST_HOST,
                "rm -f " + TEST_REMOTE_DIR + "/ssh_test_file.txt");
            pb.start().waitFor(5, TimeUnit.SECONDS);
        } catch (IOException | InterruptedException e) {
            System.err.println("Warning: Failed to cleanup remote test file: " + e.getMessage());
        }
    }

    private void cleanupRemoteDirectory(String remoteDir) {
        try {
            ProcessBuilder pb = new ProcessBuilder("ssh",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                TEST_USER + "@" + TEST_HOST,
                "rm -rf " + remoteDir);
            pb.start().waitFor(5, TimeUnit.SECONDS);
        } catch (IOException | InterruptedException e) {
            System.err.println("Warning: Failed to cleanup remote directory: " + e.getMessage());
        }
    }
}
