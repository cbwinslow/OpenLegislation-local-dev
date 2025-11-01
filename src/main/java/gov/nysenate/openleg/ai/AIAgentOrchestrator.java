package gov.nysenate.openleg.ai;

import gov.nysenate.openleg.model.document.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * High level façade that exposes AI agent capabilities to controllers or
 * other services. It composes dedicated agents that specialize on
 * ingestion, retrieval and operations on the document model.
 */
@Component
public class AIAgentOrchestrator {

    private static final Logger logger = LoggerFactory.getLogger(AIAgentOrchestrator.class);

    private final AIIngestionAgent ingestionAgent;
    private final AIRetrievalAgent retrievalAgent;
    private final AIOperationsAgent operationsAgent;

    public AIAgentOrchestrator(AIIngestionAgent ingestionAgent,
                               AIRetrievalAgent retrievalAgent,
                               AIOperationsAgent operationsAgent) {
        this.ingestionAgent = ingestionAgent;
        this.retrievalAgent = retrievalAgent;
        this.operationsAgent = operationsAgent;
    }

    /**
     * Ingest documents from an external RSS feed.
     * @param url RSS feed URL (must not be null or empty)
     * @param source Source identifier (must not be null or empty)
     * @throws IllegalArgumentException if url or source is null or empty
     */
    public void ingestExternalFeed(String url, String source) {
        if (url == null || url.isBlank() || source == null || source.isBlank()) {
            throw new IllegalArgumentException("URL and source must not be null or empty");
        }
        logger.info("Orchestrator ingesting feed {}", source);
        ingestionAgent.ingestFeed(url, source);
    }

    /**
     * Refresh all curated document sources configured in the ingestion service.
     */
    public void refreshCuratedSources() {
        logger.info("Orchestrator refreshing curated sources");
        ingestionAgent.ingestKnownSources();
    }

    public List<Document> searchDocuments(String query, int limit) {
        return retrievalAgent.search(query, limit);
    }

    public Optional<Document> findDocumentByUrl(String url) {
        return retrievalAgent.findByUrl(url);
    }

    public Map<String, Long> getDocumentCountsBySource() {
        return operationsAgent.countDocumentsBySource();
    }

    public Optional<Document> updateDocumentMetadata(Long id, String metadataJson) {
        return operationsAgent.updateMetadata(id, metadataJson);
    }

    public List<Document> getDocumentsNeedingAttention(LocalDateTime threshold) {
        return operationsAgent.getDocumentsNeedingAttention(threshold);
    }

    public List<Document> getRecentDocumentsForSource(String source, int limit) {
        return retrievalAgent.findRecentBySource(source, limit);
    }
}
