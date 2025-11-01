package gov.nysenate.openleg.ai;

import gov.nysenate.openleg.service.ingestion.IngestionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * Wraps {@link IngestionService} with domain specific semantics for AI flows.
 * Allows orchestrators to trigger targeted ingestion tasks or ad-hoc pulls
 * without interacting with scheduling annotations directly.
 */
@Component
public class AIIngestionAgent {

    private static final Logger logger = LoggerFactory.getLogger(AIIngestionAgent.class);

    private final IngestionService ingestionService;

    public AIIngestionAgent(IngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    /**
     * Trigger ingestion for an arbitrary RSS endpoint.
     */
    public void ingestFeed(String rssUrl, String source) {
        logger.info("AIIngestionAgent ingesting '{}' from {}", source, rssUrl);
        ingestionService.ingestFromRSS(rssUrl, source);
    }

    /**
     * Use the curated ingestion jobs that already exist in {@link IngestionService}.
     * Each ingestion is wrapped in error handling to ensure remaining sources are processed.
     */
    public void ingestKnownSources() {
        logger.info("AIIngestionAgent ingesting known sources");
        
        try {
            ingestionService.ingestWikiLeaks();
        } catch (Exception e) {
            logger.error("Failed to ingest WikiLeaks", e);
        }
        
        try {
            ingestionService.ingestCDC();
        } catch (Exception e) {
            logger.error("Failed to ingest CDC", e);
        }
        
        try {
            ingestionService.ingestWhiteHouse();
        } catch (Exception e) {
            logger.error("Failed to ingest White House", e);
        }
        
        try {
            ingestionService.ingestReuters();
        } catch (Exception e) {
            logger.error("Failed to ingest Reuters", e);
        }
    }
}
