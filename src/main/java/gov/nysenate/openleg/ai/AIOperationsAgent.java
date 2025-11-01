package gov.nysenate.openleg.ai;

import gov.nysenate.openleg.dao.document.DocumentRepository;
import gov.nysenate.openleg.model.document.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * Performs data model manipulations on behalf of orchestration layers.
 */
@Component
public class AIOperationsAgent {

    private static final Logger logger = LoggerFactory.getLogger(AIOperationsAgent.class);

    private final AIDataContext dataContext;
    private final DocumentRepository documentRepository;

    public AIOperationsAgent(AIDataContext dataContext, DocumentRepository documentRepository) {
        this.dataContext = dataContext;
        this.documentRepository = documentRepository;
    }

    /**
     * Count documents grouped by source using database aggregation.
     */
    public Map<String, Long> countDocumentsBySource() {
        List<Object[]> results = documentRepository.countDocumentsBySource();
        return results.stream()
                .collect(Collectors.toMap(
                        row -> (String) row[0],
                        row -> ((Number) row[1]).longValue()
                ));
    }

    public Optional<Document> updateMetadata(Long id, String metadataJson) {
        Optional<Document> maybeDoc = dataContext.getDocumentById(id);

        maybeDoc.ifPresent(doc -> {
            doc.setMetadata(metadataJson);
            doc.setCreatedAt(Optional.ofNullable(doc.getCreatedAt()).orElse(LocalDateTime.now()));
            dataContext.saveDocument(doc);
            logger.info("Updated metadata for document {}", id);
        });
        return maybeDoc;
    }

    /**
     * Get documents needing attention using database filtering.
     */
    public List<Document> getDocumentsNeedingAttention(LocalDateTime threshold) {
        return documentRepository.findDocumentsBeforeDate(threshold);
    }
}
