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

    public void ingestExternalFeed(String url, String source) {
        logger.info("Orchestrator ingesting feed {}", source);
        ingestionAgent.ingestFeed(url, source);
    }

    public void refreshCuratedSources() {
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
