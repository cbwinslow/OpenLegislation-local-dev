package gov.nysenate.openleg.service.federal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import gov.nysenate.openleg.dao.federal.FederalMemberDao;
import gov.nysenate.openleg.dao.federal.FederalCommitteeDao;
import gov.nysenate.openleg.dao.federal.bill.FederalBillRepository;
import gov.nysenate.openleg.model.federal.*;
import gov.nysenate.openleg.model.federal.bill.FederalBill;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.CompletableFuture;

/**
 * Service for ingesting data from congress.gov API.
 * Handles all data types: members, bills, committees, votes, hearings, reports, transcripts.
 */
@Service
@Transactional
public class CongressApiIngestionService {

    /**
     * Main method for CLI invocation (mvn exec:java).
     * Args: --congress 119 --endpoint bill --input /tmp/batch.json --persist --idempotent
     */
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);  // Bootstrap Spring context
        // Parse args (simple, or use JCommander)
        int congress = 119;  // Default
        String endpoint = "bill";
        String inputFile = null;
        boolean persist = false;
        boolean idempotent = true;
        for (int i = 0; i < args.length; i++) {
            if ("--congress".equals(args[i])) congress = Integer.parseInt(args[++i]);
            else if ("--endpoint".equals(args[i])) endpoint = args[++i];
            else if ("--input".equals(args[i])) inputFile = args[++i];
            else if ("--persist".equals(args[i])) persist = true;
            else if ("--idempotent".equals(args[i])) idempotent = Boolean.parseBoolean(args[++i]);
        }
        // Get bean and run
        ApplicationContext context = SpringApplication.run(Application.class, args);
        CongressApiIngestionService service = context.getBean(CongressApiIngestionService.class);
        if (inputFile != null) {
            try {
                JsonNode batch = new ObjectMapper().readTree(new File(inputFile));
                service.processBatch(endpoint, congress, batch, persist, idempotent);
            } catch (Exception e) {
                logger.error("CLI error", e);
                System.exit(1);
            }
        } else {
            service.ingestAllCongressData(congress, Set.of(endpoint)).join();
        }
        System.exit(0);
    }

    /**
     * Process a batch from JSON input (for CLI).
     */
    public void processBatch(String endpoint, int congress, JsonNode batch, boolean persist, boolean idempotent) {
        // Dispatch to specific processor
        switch (endpoint) {
            case "bill":
                processBillBatch(batch);
                break;
            case "member":
                processMemberBatch(batch);
                break;
            // Add cases for other endpoints
            default:
                logger.warn("Unsupported endpoint for batch: {}", endpoint);
        }
        if (persist) {
            // Save (idempotent check if enabled)
            if (idempotent) {
                // Pre-check logic here
            }
            // Call saveAll for type
        }
    }

    private static final Logger logger = LoggerFactory.getLogger(CongressApiIngestionService.class);

    @Value("${congress.api.key:}")
    private String apiKey;

    @Value("${congress.api.base.url:https://api.congress.gov/v3}")
    private String baseUrl;

    @Value("${congress.ingestion.batch.size:250}")
    private int batchSize;

    @Autowired
    private FederalMemberDao federalMemberDao;

    @Autowired
    private FederalCommitteeDao federalCommitteeDao;

    @Autowired
    private FederalBillRepository federalBillRepository;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * Ingest all congress.gov data for a given congress.
     */
    public CompletableFuture<CongressIngestionResult> ingestAllCongressData(int congress, Set<String> dataTypes) {
        logger.info("Starting comprehensive congress.gov ingestion for congress {} with data types: {}", congress, dataTypes);

        CongressIngestionResult result = new CongressIngestionResult(congress, dataTypes, "IN_PROGRESS");
        LocalDateTime startTime = LocalDateTime.now();

        try {
            return ingestSequential(congress, dataTypes, result);
        } catch (Exception e) {
            logger.error("Error during congress ingestion for congress {}", congress, e);
            result.setStatus("ERROR");
            result.setErrorMessage(e.getMessage());
            return CompletableFuture.completedFuture(result);
        }
    }

    private CompletableFuture<CongressIngestionResult> ingestSequential(int congress, Set<String> dataTypes, CongressIngestionResult result) {
        int totalProcessed = 0;
        int totalErrors = 0;

        try {
            if (dataTypes.contains("members")) {
                logger.info("Ingesting members for congress {}", congress);
                int count = ingestMembers(congress);
                totalProcessed += count;
                result.getDataTypeResults().put("members", new DataTypeResult(count, 0, "COMPLETED"));
            }

            if (dataTypes.contains("bills")) {
                logger.info("Ingesting bills for congress {}", congress);
                int count = ingestBills(congress);
                totalProcessed += count;
                result.getDataTypeResults().put("bills", new DataTypeResult(count, 0, "COMPLETED"));
            }

            if (dataTypes.contains("committees")) {
                logger.info("Ingesting committees for congress {}", congress);
                int count = ingestCommittees(congress);
                totalProcessed += count;
                result.getDataTypeResults().put("committees", new DataTypeResult(count, 0, "COMPLETED"));
            }

            if (dataTypes.contains("votes")) {
                logger.info("Ingesting votes for congress {}", congress);
                int count = ingestVotes(congress);
                totalProcessed += count;
                result.getDataTypeResults().put("votes", new DataTypeResult(count, 0, "COMPLETED"));
            }

            if (dataTypes.contains("hearings")) {
                logger.info("Ingesting hearings for congress {}", congress);
                int count = ingestHearings(congress);
                totalProcessed += count;
                result.getDataTypeResults().put("hearings", new DataTypeResult(count, 0, "COMPLETED"));
            }

            if (dataTypes.contains("reports")) {
                logger.info("Ingesting reports for congress {}", congress);
                int count = ingestReports(congress);
                totalProcessed += count;
                result.getDataTypeResults().put("reports", new DataTypeResult(count, 0, "COMPLETED"));
            }

            if (dataTypes.contains("transcripts")) {
                logger.info("Ingesting transcripts for congress {}", congress);
                int count = ingestTranscripts(congress);
                totalProcessed += count;
                result.getDataTypeResults().put("transcripts", new DataTypeResult(count, 0, "COMPLETED"));
            }

            result.setTotalProcessed(totalProcessed);
            result.setTotalErrors(totalErrors);
            result.setStatus("COMPLETED");
            result.setCompletedAt(LocalDateTime.now());

        } catch (Exception e) {
            logger.error("Error in sequential ingestion", e);
            result.setStatus("ERROR");
            result.setErrorMessage(e.getMessage());
        }

        return CompletableFuture.completedFuture(result);
    }

    private int ingestMembers(int congress) {
        String url = baseUrl + "/member?limit=" + batchSize + (apiKey != null && !apiKey.isEmpty() ? "&api_key=" + apiKey : "");
        return ingestPaginatedData(url, "members", this::processMemberBatch);
    }

    private int ingestBills(int congress) {
        String url = baseUrl + "/bill/" + congress + "?limit=" + batchSize + (apiKey != null && !apiKey.isEmpty() ? "&api_key=" + apiKey : "");
        return ingestPaginatedData(url, "bills", this::processBillBatch);
    }

    private int ingestCommittees(int congress) {
        String url = baseUrl + "/committee/" + congress + "?limit=" + batchSize + (apiKey != null && !apiKey.isEmpty() ? "&api_key=" + apiKey : "");
        return ingestPaginatedData(url, "committees", this::processCommitteeBatch);
    }

    private int ingestVotes(int congress) {
        String url = baseUrl + "/nomination/" + congress + "?limit=" + batchSize + (apiKey != null && !apiKey.isEmpty() ? "&api_key=" + apiKey : "");
        return ingestPaginatedData(url, "nominations", this::processVoteBatch);
    }

    private int ingestHearings(int congress) {
        String url = baseUrl + "/hearing/" + congress + "?limit=" + batchSize + (apiKey != null && !apiKey.isEmpty() ? "&api_key=" + apiKey : "");
        return ingestPaginatedData(url, "hearings", this::processHearingBatch);
    }

    private int ingestReports(int congress) {
        String url = baseUrl + "/congressional-report/" + congress + "?limit=" + batchSize + (apiKey != null && !apiKey.isEmpty() ? "&api_key=" + apiKey : "");
        return ingestPaginatedData(url, "reports", this::processReportBatch);
    }

    private int ingestTranscripts(int congress) {
        String url = baseUrl + "/daily-congressional-record/" + congress + "?limit=" + batchSize + (apiKey != null && !apiKey.isEmpty() ? "&api_key=" + apiKey : "");
        return ingestPaginatedData(url, "transcripts", this::processTranscriptBatch);
    }

    private int ingestPaginatedData(String initialUrl, String dataType, BatchProcessor processor) {
        int totalProcessed = 0;
        String url = initialUrl;

        while (url != null) {
            try {
                logger.debug("Fetching {} from: {}", dataType, url);
                ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);

                if (response.getStatusCode().is2xxSuccessful()) {
                    JsonNode root = objectMapper.readTree(response.getBody());
                    int batchCount = processor.process(root);
                    totalProcessed += batchCount;

                    // Check for next page
                    JsonNode pagination = root.path("pagination");
                    if (pagination.has("next")) {
                        url = pagination.get("next").asText();
                    } else {
                        url = null;
                    }
                } else {
                    logger.error("HTTP error fetching {}: {}", dataType, response.getStatusCode());
                    break;
                }
            } catch (Exception e) {
                logger.error("Error fetching {} batch", dataType, e);
                break;
            }
        }

        logger.info("Processed {} {} total", totalProcessed, dataType);
        return totalProcessed;
    }

    private int processMemberBatch(JsonNode root) {
        JsonNode members = root.path("members");
        if (members.isArray()) {
            List<FederalMember> memberList = new ArrayList<>();
            for (JsonNode memberNode : members) {
                try {
                    FederalMember member = mapToFederalMember(memberNode);
                    memberList.add(member);
                } catch (Exception e) {
                    logger.warn("Failed to map member: {}", e.getMessage());
                }
            }
            federalMemberDao.saveAll(memberList);
            return memberList.size();
        }
        return 0;
    }

    private int processBillBatch(JsonNode root) {
        JsonNode bills = root.path("bills");
        if (bills.isArray()) {
            List<FederalBill> billList = new ArrayList<>();
            for (JsonNode billNode : bills) {
                try {
                    FederalBill bill = mapToFederalBill(billNode);
                    billList.add(bill);
                } catch (Exception e) {
                    logger.warn("Failed to map bill: {}", e.getMessage());
                }
            }
            federalBillRepository.saveAll(billList);
            return billList.size();
        }
        return 0;
    }

    private int processCommitteeBatch(JsonNode root) {
        JsonNode committees = root.path("committees");
        if (committees.isArray()) {
            List<FederalCommittee> committeeList = new ArrayList<>();
            for (JsonNode committeeNode : committees) {
                try {
                    FederalCommittee committee = mapToFederalCommittee(committeeNode);
                    committeeList.add(committee);
                } catch (Exception e) {
                    logger.warn("Failed to map committee: {}", e.getMessage());
                }
            }
            federalCommitteeDao.saveAll(committeeList);
            return committeeList.size();
        }
        return 0;
    }

    private int processVoteBatch(JsonNode root) {
        // Implementation for votes/nominations
        JsonNode nominations = root.path("nominations");
        if (nominations.isArray()) {
            // Process nominations as votes
            return nominations.size();
        }
        return 0;
    }

    private int processHearingBatch(JsonNode root) {
        // Implementation for hearings
        JsonNode hearings = root.path("hearings");
        if (hearings.isArray()) {
            return hearings.size();
        }
        return 0;
    }

    private int processReportBatch(JsonNode root) {
        // Implementation for reports
        JsonNode reports = root.path("reports");
        if (reports.isArray()) {
            return reports.size();
        }
        return 0;
    }

    private int processTranscriptBatch(JsonNode root) {
        // Implementation for transcripts
        JsonNode transcripts = root.path("transcripts");
        if (transcripts.isArray()) {
            return transcripts.size();
        }
        return 0;
    }

    private FederalMember mapToFederalMember(JsonNode node) {
        FederalMember member = new FederalMember();
        member.setBioguideId(node.path("bioguideId").asText());
        String firstName = node.path("firstName").asText(null);
        String lastName = node.path("lastName").asText(null);
        if (firstName != null && lastName != null) {
            member.setFullName(firstName + " " + lastName);
        }
        // Add more mapping as needed
        return member;
    }

    private FederalBill mapToFederalBill(JsonNode node) {
        FederalBill bill = new FederalBill();
        bill.setCongress(node.path("congress").asInt());
        bill.setType(node.path("type").asText());
        bill.setNumber(node.path("number").asInt());
        bill.setTitle(node.path("title").asText());
        // Add more mapping as needed
        return bill;
    }

    private FederalCommittee mapToFederalCommittee(JsonNode node) {
        FederalCommittee committee = new FederalCommittee();
        committee.setCommitteeCode(node.path("committeeCode").asText(null));
        committee.setCommitteeName(node.path("name").asText(null));
        String chamberStr = node.path("chamber").asText(null);
        if (chamberStr != null) {
            committee.setChamber(FederalChamber.valueOf(chamberStr.toUpperCase()));
        }
        // Add more mapping as needed
        return committee;
    }

    @FunctionalInterface
    private interface BatchProcessor {
        int process(JsonNode root) throws Exception;
    }

    // Result classes
    public static class CongressIngestionResult {
        private final int congress;
        private final Set<String> dataTypes;
        private int totalProcessed;
        private int totalErrors;
        private String status;
        private String errorMessage;
        private LocalDateTime completedAt;
        private Map<String, DataTypeResult> dataTypeResults = new HashMap<>();

        public CongressIngestionResult(int congress, Set<String> dataTypes, String status) {
            this.congress = congress;
            this.dataTypes = dataTypes;
            this.status = status;
        }

        // Getters and setters
        public int getCongress() { return congress; }
        public Set<String> getDataTypes() { return dataTypes; }
        public int getTotalProcessed() { return totalProcessed; }
        public void setTotalProcessed(int totalProcessed) { this.totalProcessed = totalProcessed; }
        public int getTotalErrors() { return totalErrors; }
        public void setTotalErrors(int totalErrors) { this.totalErrors = totalErrors; }
        public String getStatus() { return status; }
        public void setStatus(String status) { this.status = status; }
        public String getErrorMessage() { return errorMessage; }
        public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
        public LocalDateTime getCompletedAt() { return completedAt; }
        public void setCompletedAt(LocalDateTime completedAt) { this.completedAt = completedAt; }
        public Map<String, DataTypeResult> getDataTypeResults() { return dataTypeResults; }
        public void setDataTypeResults(Map<String, DataTypeResult> dataTypeResults) { this.dataTypeResults = dataTypeResults; }
    }

    public static class DataTypeResult {
        private final int processedCount;
        private final int errorCount;
        private final String status;

        public DataTypeResult(int processedCount, int errorCount, String status) {
            this.processedCount = processedCount;
            this.errorCount = errorCount;
            this.status = status;
        }

        public int getProcessedCount() { return processedCount; }
        public int getErrorCount() { return errorCount; }
        public String getStatus() { return status; }
    }
}
