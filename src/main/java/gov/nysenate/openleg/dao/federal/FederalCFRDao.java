package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalCFR;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Data access layer for federal CFR operations.
 */
@Repository
public interface FederalCFRDao extends JpaRepository<FederalCFR, Long> {

    /**
     * Find CFR sections by title.
     */
    List<FederalCFR> findByTitleOrderByPartAsc(Integer title);

    /**
     * Find CFR sections by title and part.
     */
    List<FederalCFR> findByTitleAndPartOrderBySectionAsc(Integer title, Integer part);

    /**
     * Find a specific CFR section.
     */
    List<FederalCFR> findByTitleAndPartAndSection(Integer title, Integer part, String section);

    /**
     * Search CFR sections by text content (case-insensitive partial match).
     */
    @Query("SELECT c FROM FederalCFR c WHERE " +
           "LOWER(c.sectionText) LIKE LOWER(CONCAT('%', :text, '%')) " +
           "ORDER BY c.title, c.part, c.section")
    List<FederalCFR> searchByText(@Param("text") String text);

    /**
     * Get count of sections by title.
     */
    @Query("SELECT COUNT(c) FROM FederalCFR c WHERE c.title = :title")
    long countByTitle(@Param("title") Integer title);

    /**
     * Get count of sections by title and part.
     */
    @Query("SELECT COUNT(c) FROM FederalCFR c WHERE c.title = :title AND c.part = :part")
    long countByTitleAndPart(@Param("title") Integer title, @Param("part") Integer part);
}