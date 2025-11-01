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

    /**
     * Constructs an AIAgentOrchestrator that composes ingestion, retrieval, and operations agents.
     *
     * @param ingestionAgent  agent responsible for ingesting external feeds and known sources
     * @param retrievalAgent  agent responsible for searching and retrieving documents
     * @param operationsAgent agent responsible for document operations such as counts and metadata updates
     */
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

    /**
     * Searches for documents that match the provided query.
     *
     * @param query the search query or expression to match documents against
     * @param limit the maximum number of documents to return
     * @return a list of matching Document objects; may be empty
     */
    public List<Document> searchDocuments(String query, int limit) {
        return retrievalAgent.search(query, limit);
    }

    /**
     * Locate a document using its canonical URL.
     *
     * @param url the document's canonical URL to look up
     * @return an Optional containing the matched Document if found, empty otherwise
     */
    public Optional<Document> findDocumentByUrl(String url) {
        return retrievalAgent.findByUrl(url);
    }

    /**
     * Retrieves document counts grouped by source.
     *
     * @return a map where keys are source identifiers and values are the number of documents for that source
     */
    public Map<String, Long> getDocumentCountsBySource() {
        return operationsAgent.countDocumentsBySource();
    }

    /**
     * Update metadata for the document with the given id.
     *
     * @param id           the unique identifier of the document to update
     * @param metadataJson a JSON string containing metadata fields to set on the document
     * @return             an Optional containing the updated Document if the document was found and updated, otherwise empty
     */
    public Optional<Document> updateDocumentMetadata(Long id, String metadataJson) {
        return operationsAgent.updateMetadata(id, metadataJson);
    }

    /**
     * Retrieve documents that require review or action based on the given time threshold.
     *
     * @param threshold the cutoff LocalDateTime used to determine which documents need attention
     * @return a list of documents that meet the attention criteria; an empty list if none are found
     */
    public List<Document> getDocumentsNeedingAttention(LocalDateTime threshold) {
        return operationsAgent.getDocumentsNeedingAttention(threshold);
    }

    /**
     * Fetches the most recently added documents for the specified source.
     *
     * @param source the source identifier to filter documents by
     * @param limit the maximum number of documents to return
     * @return a list of documents for the source ordered from most recent to least recent
     */
    public List<Document> getRecentDocumentsForSource(String source, int limit) {
        return retrievalAgent.findRecentBySource(source, limit);
    }
}