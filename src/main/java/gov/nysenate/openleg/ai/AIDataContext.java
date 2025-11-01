package gov.nysenate.openleg.ai;

import gov.nysenate.openleg.dao.document.DocumentRepository;
import gov.nysenate.openleg.model.document.Document;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Centralizes access to persisted legislative documents for AI agents.
 * Provides convenience helpers for fetching and updating content that
 * agents can operate on without duplicating repository logic.
 */
@Component
public class AIDataContext {

    private final DocumentRepository documentRepository;

    /**
     * Create a new AIDataContext backed by the provided DocumentRepository.
     *
     * The repository is used for persistence operations on Document entities.
     *
     * @param documentRepository the repository used to load and save documents
     */
    public AIDataContext(DocumentRepository documentRepository) {
        this.documentRepository = documentRepository;
    }

    /**
     * Persist a document generated or enriched by an agent, ensuring its creation timestamp is set.
     *
     * If the document's createdAt is null, sets it to the current time before saving.
     *
     * @param document the Document to persist
     * @return the persisted Document with persistence-managed fields populated (for example, `id` and `createdAt`)
     */
    public Document saveDocument(Document document) {
        if (document.getCreatedAt() == null) {
            document.setCreatedAt(LocalDateTime.now());
        }
        return documentRepository.save(document);
    }

    /**
     * Find a persisted Document by its URL.
     *
     * @param url the document URL to search for
     * @return an Optional containing the matching Document, or empty if none is found
     */
    public Optional<Document> getDocumentByUrl(String url) {
        return documentRepository.findByUrl(url);
    }

    /**
     * Retrieve the document with the given identifier.
     *
     * @param id the document's identifier
     * @return an Optional containing the Document if found, empty otherwise
     */
    public Optional<Document> getDocumentById(Long id) {
        return documentRepository.findById(id);
    }

    /**
     * Retrieve all persisted documents that originate from the given source.
     *
     * @param source the source identifier used to filter documents
     * @return a list of documents from the specified source (empty if none found)
     */
    public List<Document> getDocumentsBySource(String source) {
        return documentRepository.findBySource(source);
    }

    /**
     * Retrieve all persisted Document entities.
     *
     * @return the list of all stored Document entities, or an empty list if none exist
     */
    public List<Document> getAllDocuments() {
        return documentRepository.findAll();
    }
}