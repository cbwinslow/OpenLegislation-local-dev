package gov.nysenate.openleg.service.ingestion.federal;

import com.fasterxml.jackson.databind.ObjectMapper;
import gov.nysenate.openleg.dao.federal.bill.FederalBillRepository;
import gov.nysenate.openleg.model.federal.bill.FederalBill;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Service
@Transactional
public class FederalBillIngestionService {
    private static final Logger logger = LoggerFactory.getLogger(FederalBillIngestionService.class);

    @Autowired
    private FederalBillRepository billRepository;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();  // For JSON

    /**
     * Ingest bills from Congress.gov API (e.g., recent introduced bills).
     * API key optional; rate-limited to 1000 req/day without.
     */
    public void ingestCongressBills(String apiKey, Integer congress, String type, Integer limit) {
        String url = "https://api.congress.gov/v3/bill/" + congress + "/" + type + "?limit=" + limit +
                     (apiKey != null ? "&api_key=" + apiKey : "");
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            if (response.getStatusCode().is2xxSuccessful()) {
                Map<String, Object> body = response.getBody();
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> bills = (List<Map<String, Object>>) body.get("bills");  // Adjust path per API

                List<FederalBill> newBills = bills.stream()
                    .filter(billMap -> !billRepository.existsBySourceUrl((String) billMap.get("congressUrl")))
                    .map(this::mapToFederalBill)
                    .toList();

                billRepository.saveAll(newBills);
                logger.info("Ingested {} new federal bills for congress {}, type {}", newBills.size(), congress, type);
            }
        } catch (Exception e) {
            logger.error("Error ingesting Congress bills: {}", e.getMessage(), e);
        }
    }

    private FederalBill mapToFederalBill(Map<String, Object> billData) {
        FederalBill bill = new FederalBill();
        bill.setCongress(((Number) billData.get("congress")).intValue());
        bill.setType((String) billData.get("billType"));
        bill.setNumber(((Number) billData.get("number")).intValue());
        bill.setTitle((String) billData.get("title"));
        bill.setSummary((String) billData.get("summary"));
        @SuppressWarnings("unchecked")
        Map<String, Object> latestAction = (Map<String, Object>) billData.get("latestAction");
        bill.setStatus((String) latestAction.get("actionStatus"));
        // Parse dates, sponsor, etc. (use LocalDateTime.parse if ISO strings)
        // Note: Assuming introducedDate is a string in ISO format; adjust as needed
        String introducedDateStr = (String) billData.get("introducedDate");
        if (introducedDateStr != null) {
            bill.setIntroducedDate(LocalDateTime.parse(introducedDateStr));
        }
        bill.setSourceUrl((String) billData.get("congressUrl"));
        bill.setFullText(extractText(billData));  // Custom method to parse text/summaryInXml
        try {
            bill.setMetadata(objectMapper.writeValueAsString(billData));  // Full JSON
        } catch (Exception e) {
            logger.warn("Failed to serialize metadata for bill: {}", e.getMessage());
            bill.setMetadata("{}");
        }
        return bill;
    }

    private String extractText(Map<String, Object> billData) {
        // Logic to get text from 'text' or 'summaries' fields; fetch full if needed via another API call
        // For now, use summary as fallback
        return (String) billData.getOrDefault("summary", "No text available");
    }

    /**
     * Scheduled ingestion example (e.g., daily for new bills).
     */
    @Scheduled(cron = "0 0 2 * * ?")  // Daily at 2 AM
    public void scheduledIngestRecentBills() {
        ingestCongressBills(null, 118, "hr", 100);  // No API key, House bills, limit 100
    }

    // For GovInfo bulk: Download XML/ZIP, parse with JAXB (see pom.xml JAXB plugin for USLM XSDs)
    // Example: Use XmlMapper or SAX for large files, then map to FederalBill
}