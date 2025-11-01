package gov.nysenate.openleg.ai;

import gov.nysenate.openleg.dao.document.DocumentRepository;
import gov.nysenate.openleg.model.document.Document;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * Centralizes access to persisted legislative documents for AI agents.
 * Provides convenience helpers for fetching and updating content that
 * agents can operate on without duplicating repository logic.
 */
@Component
public class AIDataContext {

    private final DocumentRepository documentRepository;

    public AIDataContext(DocumentRepository documentRepository) {
        this.documentRepository = documentRepository;
    }

    /**
     * Persist a new document that has been generated or enriched by an agent.
     */
    public Document saveDocument(Document document) {
        if (document.getCreatedAt() == null) {
            document.setCreatedAt(LocalDateTime.now());
        }
        return documentRepository.save(document);
    }

    /**
     * Retrieve a document by url if one exists.
     */
    public Optional<Document> getDocumentByUrl(String url) {
        return documentRepository.findByUrl(url);
    }

    /**
     * Retrieve a document by identifier.
     */
    public Optional<Document> getDocumentById(Long id) {
        return documentRepository.findById(id);
    }

    /**
     * Fetch all documents from a particular source so that downstream
     * agents can perform analytics or summarization.
     */
    public List<Document> getDocumentsBySource(String source) {
        return documentRepository.findBySource(source);
    }

    /**
     * Count documents grouped by source using efficient database aggregation.
     */
    public Map<String, Long> countDocumentsBySource() {
        List<Object[]> results = documentRepository.countBySourceGrouped();
        return results.stream()
                .collect(Collectors.toMap(
                        row -> (String) row[0],
                        row -> (Long) row[1]
                ));
    }

    /**
     * Find documents that need attention based on publication date threshold.
     */
    public List<Document> getDocumentsNeedingAttention(LocalDateTime threshold) {
        return documentRepository.findDocumentsNeedingAttention(threshold);
    }
}
