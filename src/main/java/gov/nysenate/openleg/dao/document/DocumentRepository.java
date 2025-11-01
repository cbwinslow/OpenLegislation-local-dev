package gov.nysenate.openleg.dao.document;

import gov.nysenate.openleg.model.document.Document;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Repository
public interface DocumentRepository extends JpaRepository<Document, Long> {

    /**
     * Find documents by source.
     */
    List<Document> findBySource(String source);

    /**
     * Find document by URL (unique).
     */
    Optional<Document> findByUrl(String url);

    /**
     * Find recent documents from a source, ordered by pub_date.
     */
    @Query("SELECT d FROM Document d WHERE d.source = :source ORDER BY d.pubDate DESC")
    List<Document> findRecentBySource(@Param("source") String source, Pageable pageable);

    /**
     * Perform a fuzzy keyword search across title, description and content fields.
     */
    @Query(
        value = "SELECT * FROM document d " +
                "WHERE to_tsvector('english', coalesce(d.title,'') || ' ' || coalesce(d.description,'') || ' ' || coalesce(d.content,'')) " +
                "   @@ to_tsquery('english', :query) " +
                "ORDER BY d.pub_date DESC",
        nativeQuery = true)
    List<Document> searchByKeyword(@Param("query") String query, Pageable pageable);

    /**
     * Check if document exists by URL to ensure idempotency.
     */
    boolean existsByUrl(String url);

    /**
     * Count documents grouped by source.
     */
    @Query("SELECT d.source as source, COUNT(d) as count FROM Document d WHERE d.source IS NOT NULL GROUP BY d.source")
    List<SourceCount> countBySource();

    /**
     * Find documents that need attention (missing pubDate or pubDate before threshold).
     */
    @Query("SELECT d FROM Document d WHERE d.pubDate IS NULL OR d.pubDate < :threshold")
    List<Document> findDocumentsNeedingAttention(@Param("threshold") LocalDateTime threshold);

    /**
     * Projection interface for source count aggregation.
     */
    interface SourceCount {
        String getSource();
        Long getCount();
    }
}
