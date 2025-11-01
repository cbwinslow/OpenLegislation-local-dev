package gov.nysenate.openleg.ai;

import gov.nysenate.openleg.dao.document.DocumentRepository;
import gov.nysenate.openleg.model.document.Document;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Component;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * Provides semantic retrieval primitives that can later be wired into
 * retrieval augmented generation workflows.
 */
@Component
public class AIRetrievalAgent {

    private final DocumentRepository documentRepository;

    /**
     * Create an AIRetrievalAgent backed by the given document repository.
     *
     * @param documentRepository repository used to retrieve and search Document entities
     */
    public AIRetrievalAgent(DocumentRepository documentRepository) {
        this.documentRepository = documentRepository;
    }

    /**
     * Finds a document with the specified URL.
     *
     * @param url the document's URL
     * @return an Optional containing the matching Document if present, `Optional.empty()` otherwise
     */
    public Optional<Document> findByUrl(String url) {
        return documentRepository.findByUrl(url);
    }

    /**
     * Retrieve the most recent documents for a given source, sorted by publication date (newest first)
     * and then by creation date (newest first), with null dates ordered last.
     *
     * @param source the source identifier to filter documents by
     * @param limit  the maximum number of documents to return
     * @return a list of up to {@code limit} documents from {@code source}, ordered by pubDate then createdAt as described
     */
    public List<Document> findRecentBySource(String source, int limit) {
        return documentRepository.findBySource(source).stream()
                .sorted(Comparator.comparing(Document::getPubDate, Comparator.nullsLast(Comparator.reverseOrder()))
                        .thenComparing(Document::getCreatedAt, Comparator.nullsLast(Comparator.reverseOrder())))
                .limit(limit)
                .collect(Collectors.toList());
    }

    /**
     * Searches documents by the given keyword and returns up to the specified number of matches.
     *
     * @param query the keyword query to search for
     * @param limit the maximum number of documents to return
     * @return a list of documents matching the query, containing at most `limit` entries
     */
    public List<Document> search(String query, int limit) {
        return documentRepository.searchByKeyword(query, PageRequest.of(0, limit));
    }
}