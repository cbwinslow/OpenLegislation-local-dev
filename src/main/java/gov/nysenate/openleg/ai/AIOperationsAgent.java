package gov.nysenate.openleg.ai;

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

    /**
     * Create an AIOperationsAgent configured with the provided AIDataContext for document data operations.
     *
     * @param dataContext the data context used to retrieve and persist documents
     */
    public AIOperationsAgent(AIDataContext dataContext) {
        this.dataContext = dataContext;
    }

    /**
     * Count documents grouped by their non-null source.
     *
     * @return a map mapping each non-null document source to the number of documents from that source
     */
    public Map<String, Long> countDocumentsBySource() {
        return dataContext.getAllDocuments().stream()
                .filter(doc -> doc.getSource() != null)
                .collect(Collectors.groupingBy(Document::getSource, Collectors.counting()));
    }

    /**
     * Update a document's metadata and persist the change if the document exists.
     *
     * If a document with the given id exists, its metadata is replaced with the provided JSON,
     * createdAt is set to the current time if it was previously null, and the updated document is saved.
     *
     * @param id the identifier of the document to update
     * @param metadataJson the metadata JSON string to set on the document
     * @return the updated Document wrapped in an Optional if a document with the given id existed, otherwise an empty Optional
     */
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
     * Retrieves documents that require attention based on publication date.
     *
     * @param threshold the cutoff LocalDateTime; documents with a null publication date or a pubDate before this threshold are considered in need of attention
     * @return a list of documents whose `pubDate` is null or earlier than the given threshold
     */
    public List<Document> getDocumentsNeedingAttention(LocalDateTime threshold) {
        return dataContext.getAllDocuments().stream()
                .filter(doc -> doc.getPubDate() == null || doc.getPubDate().isBefore(threshold))
                .collect(Collectors.toList());
    }
}