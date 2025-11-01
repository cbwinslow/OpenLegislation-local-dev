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
 * Performs data model manipulations on behalf of orchestration layers.
 */
@Component
public class AIOperationsAgent {

    private static final Logger logger = LoggerFactory.getLogger(AIOperationsAgent.class);

    private final AIDataContext dataContext;

    public AIOperationsAgent(AIDataContext dataContext) {
        this.dataContext = dataContext;
    }

    /**
     * Returns a count of documents grouped by source.
     * Uses database aggregation for efficiency.
     */
    public Map<String, Long> countDocumentsBySource() {
        return dataContext.countDocumentsBySource();
    }

    public Optional<Document> updateMetadata(Long id, String metadataJson) {
        Optional<Document> maybeDoc = dataContext.getDocumentById(id);

        maybeDoc.ifPresent(doc -> {
            doc.setMetadata(metadataJson);
            dataContext.saveDocument(doc);
            logger.info("Updated metadata for document {}", id);
        });
        return maybeDoc;
    }

    /**
     * Find documents that need attention (missing pubDate or pubDate before threshold).
     * Uses database query for efficiency.
     */
    public List<Document> getDocumentsNeedingAttention(LocalDateTime threshold) {
        return dataContext.getDocumentsNeedingAttention(threshold);
    }
}
