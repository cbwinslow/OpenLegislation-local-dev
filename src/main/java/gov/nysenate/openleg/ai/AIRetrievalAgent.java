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

    public AIRetrievalAgent(DocumentRepository documentRepository) {
        this.documentRepository = documentRepository;
    }

    public Optional<Document> findByUrl(String url) {
        return documentRepository.findByUrl(url);
    }

    public List<Document> findRecentBySource(String source, int limit) {
        return documentRepository.findBySource(source).stream()
                .sorted(Comparator.comparing(Document::getPubDate, Comparator.nullsLast(Comparator.reverseOrder()))
                        .thenComparing(Document::getCreatedAt, Comparator.nullsLast(Comparator.reverseOrder())))
                .limit(limit)
                .collect(Collectors.toList());
    }

    public List<Document> search(String query, int limit) {
        return documentRepository.searchByKeyword(query, PageRequest.of(0, limit));
    }
}
