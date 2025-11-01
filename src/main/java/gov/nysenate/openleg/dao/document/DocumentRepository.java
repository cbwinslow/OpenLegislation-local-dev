package gov.nysenate.openleg.dao.document;

import gov.nysenate.openleg.model.document.Document;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
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
     * Retrieve documents from the given source ordered by publication date (newest first).
     *
     * @param source the document source identifier to filter by
     * @param limit  maximum number of documents to return
     * @return       a list of documents from the specified source ordered by `pubDate` descending
     */
    @Query("SELECT d FROM Document d WHERE d.source = :source ORDER BY d.pubDate DESC")
    List<Document> findRecentBySource(@Param("source") String source, int limit);

    /**
     * Search documents by a PostgreSQL full-text tsquery across title, description, and content.
     *
     * @param query    a PostgreSQL `tsquery` expression to match against the combined text fields
     * @param pageable paging and sorting parameters for the result set
     * @return         a list of Documents matching the query, ordered by publication date (newest first)
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
}