package gov.nysenate.openleg.processors.federal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import gov.nysenate.openleg.dao.bill.data.BillDao;
import gov.nysenate.openleg.legislation.bill.Bill;
import gov.nysenate.openleg.legislation.bill.BillAction;
import gov.nysenate.openleg.legislation.bill.BillSponsor;
import gov.nysenate.openleg.model.BaseBillId;
import gov.nysenate.openleg.model.process.ProcessUnit;
import gov.nysenate.openleg.service.process.LegDataProcessor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Component
public class GovInfoApiProcessor implements LegDataProcessor, CommandLineRunner {

    @Value("${govinfo.api.key:dummy}")
    private String apiKey;

    private static final Logger logger = LoggerFactory.getLogger(GovInfoApiProcessor.class);

    @Autowired
    private BillDao billDao;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    public List<Bill> processBills(String congress) {
        logger.info("Starting ingestion of bills for congress: {}", congress);
        String url = "https://api.govinfo.gov/v1/search?collection=BILLS&congress=" + congress + "&api_key=" + apiKey + "&limit=50";
        List<Bill> bills = new ArrayList<>();
        int retryCount = 0;
        int maxRetries = 3;
        while (retryCount < maxRetries) {
            try {
                logger.debug("Fetching from URL: {}", url);
                ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
                if (response.getStatusCode().is2xxSuccessful()) {
                    JsonNode root = objectMapper.readTree(response.getBody());
                    if (root.path("status").asText("ok").equals("error")) {
                        logger.error("API returned error: {}", root.path("message").asText());
                        throw new RuntimeException("API error: " + root.path("message").asText());
                    }
                    JsonNode results = root.path("search").path("results");
                    int processed = 0;
                    for (JsonNode hit : results) {
                        try {
                            Bill bill = mapBillFromJson(hit, congress);
                            billDao.updateBillVersion(bill, new ProcessUnit(LocalDateTime.now(), "GovInfo API Ingestion"));
                            bills.add(bill);
                            processed++;
                            logger.debug("Processed bill: {}", bill.getBillId());
                        } catch (Exception parseEx) {
                            logger.warn("Failed to parse bill from hit: {}", hit, parseEx);
                        }
                    }
                    logger.info("Successfully processed {} bills for congress {}", processed, congress);
                    break; // Success, exit retry loop
                } else {
                    logger.warn("HTTP error: {}", response.getStatusCode());
                }
            } catch (Exception e) {
                retryCount++;
                logger.warn("Attempt {} failed for congress {}: {}", retryCount, congress, e.getMessage());
                if (retryCount >= maxRetries) {
                    logger.error("Max retries exceeded for congress {}", congress, e);
                    throw new RuntimeException("Failed to fetch bills after " + maxRetries + " retries", e);
                }
                try {
                    Thread.sleep(1000 * retryCount); // Exponential backoff
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException("Interrupted during retry", ie);
                }
            }
        }
        logger.info("Ingestion completed for congress {}: {} bills ingested", congress, bills.size());
        return bills;
    }

    private Bill mapBillFromJson(JsonNode hit, String congressStr) {
        Bill bill = new Bill();
        BaseBillId billId = new BaseBillId();
        billId.setSessionId(congressToSessionYear(Integer.parseInt(congressStr)));
        String titleText = hit.path("title").asText();
        billId.setBillNo(titleText.split(" ")[0]);  // e.g., "HR 1"
        bill.setBillId(billId);
        bill.setTitle(titleText);
        bill.setFederalCongress(Integer.parseInt(congressStr));
        bill.setFederalSource("GovInfo API");

        // Sponsors
        List<BillSponsor> sponsors = new ArrayList<>();
        JsonNode sponsorsNode = hit.path("metadata").path("sponsors");
        if (sponsorsNode.isArray()) {
            for (JsonNode sponsor : sponsorsNode) {
                BillSponsor bs = new BillSponsor();
                bs.setMemberName(sponsor.path("name").asText());
                // Add party, state if available
                Optional.ofNullable(sponsor.path("party").asText(null)).ifPresent(bs::setParty);
                Optional.ofNullable(sponsor.path("state").asText(null)).ifPresent(state -> bs.setDistrict(state)); // Approximate
                sponsors.add(bs);
            }
        }
        bill.setSponsors(sponsors);

        // Actions
        List<BillAction> actions = new ArrayList<>();
        JsonNode actionsNode = hit.path("metadata").path("actions");
        if (actionsNode.isArray()) {
            for (JsonNode action : actionsNode) {
                BillAction ba = new BillAction(LocalDateTime.parse(action.path("date").asText()), action.path("chamber").asText("Unknown"), action.path("text").asText());
                actions.add(ba);
            }
        }
        bill.setActions(actions);

        return bill;
    }

    private int congressToSessionYear(int congress) {
        // Simple mapping: 118th -> 2023-2024, but for sessionId use start year
        return 2000 + (congress - 106) * 2 - 1; // Approximate, adjust based on actual (e.g., 119 -> 2025)
    }

    // Similar methods for FR (LawDocument), CREC (Transcript), etc.
    public List<LawDocument> processFR(String query) {
        // Implementation for Federal Register
        return new ArrayList<>();
    }

    // ... other collections
}
