package gov.nysenate.openleg.controller;

import gov.nysenate.openleg.service.ingestion.IngestionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.Map;

@Controller
public class IngestionController {

    @Autowired
    private IngestionService ingestionService;

    @PostMapping("/ingest/start")
    @ResponseBody
    public Map<String, Object> startIngestion(@RequestParam String site, @RequestParam String collection, @RequestParam(required = false) String congress) {
        // Trigger ingestion based on site/collection
        String rssUrl = getRssUrl(site, collection, congress);  // Helper to get URL
        ingestionService.ingestFromRSS(rssUrl, site);
        return Map.of("status", "started", "site", site, "collection", collection);
    }

    @MessageMapping("/progress")
    @SendTo("/topic/progress")
    public Map<String, Object> getProgress() {
        // Broadcast current progress (called periodically or on event)
        // TODO: Implement actual progress tracking
        return Map.of("ingested", 0, "total", 0, "successRate", 0.0);
    }

    private String getRssUrl(String site, String collection, String congress) {
        if ("govinfo".equals(site) && "BILLS".equals(collection)) {
            return "https://api.govinfo.gov/v1/rss/collections/BILLS";  // Example RSS
        } else if ("wikileaks".equals(site)) {
            return "https://wikileaks.org/feed.xml";
        } // Add more...
        return "";
    }
}
