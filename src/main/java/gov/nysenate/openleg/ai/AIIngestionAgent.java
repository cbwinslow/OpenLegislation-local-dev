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

    /**
     * Creates an AIIngestionAgent that delegates ingestion tasks to the provided service.
     *
     * @param ingestionService the service used to perform ingestion operations invoked by this agent
     */
    public AIIngestionAgent(IngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    /**
     * Trigger ingestion for the given RSS feed and associate the ingested content with the specified source.
     *
     * @param rssUrl the RSS feed URL to ingest
     * @param source a label or identifier used to attribute the ingested content to its source
     */
    public void ingestFeed(String rssUrl, String source) {
        logger.info("AIIngestionAgent ingesting '{}' from {}", source, rssUrl);
        ingestionService.ingestFromRSS(rssUrl, source);
    }

    /**
     * Triggers ingestion for a predefined set of known sources used by AI workflows.
     *
     * <p>Invokes ingestion jobs for WikiLeaks, the CDC, the White House, and Reuters in sequence.</p>
     */
    public void ingestKnownSources() {
        logger.info("AIIngestionAgent ingesting known sources");
        ingestionService.ingestWikiLeaks();
        ingestionService.ingestCDC();
        ingestionService.ingestWhiteHouse();
        ingestionService.ingestReuters();
    }
}