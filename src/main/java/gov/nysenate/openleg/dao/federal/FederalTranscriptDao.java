package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalTranscript;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

/**
 * Data access layer for federal transcript operations.
 */
@Repository
public interface FederalTranscriptDao extends JpaRepository<FederalTranscript, Long> {

    /**
     * Find a federal transcript by its transcript ID.
     */
    List<FederalTranscript> findByTranscriptId(String transcriptId);

    /**
     * Find federal transcripts by congress.
     */
    List<FederalTranscript> findByCongressOrderByDateDesc(Integer congress);

    /**
     * Find federal transcripts by date.
     */
    List<FederalTranscript> findByDateOrderByVolumeAsc(LocalDate date);

    /**
     * Find federal transcripts by chamber.
     */
    List<FederalTranscript> findByChamberOrderByDateDesc(String chamber);

    /**
     * Find federal transcripts by date range.
     */
    @Query("SELECT t FROM FederalTranscript t WHERE t.date BETWEEN :startDate AND :endDate " +
           "ORDER BY t.date DESC, t.volume ASC")
    List<FederalTranscript> findByDateBetween(
        @Param("startDate") LocalDate startDate,
        @Param("endDate") LocalDate endDate
    );

    /**
     * Search federal transcripts by title (case-insensitive partial match).
     */
    @Query("SELECT t FROM FederalTranscript t WHERE " +
           "LOWER(t.title) LIKE LOWER(CONCAT('%', :title, '%')) " +
           "ORDER BY t.date DESC")
    List<FederalTranscript> searchByTitle(@Param("title") String title);

    /**
     * Get count of transcripts by congress.
     */
    @Query("SELECT COUNT(t) FROM FederalTranscript t WHERE t.congress = :congress")
    long countByCongress(@Param("congress") Integer congress);

    /**
     * Get count of transcripts by chamber.
     */
    @Query("SELECT COUNT(t) FROM FederalTranscript t WHERE t.chamber = :chamber")
    long countByChamber(@Param("chamber") String chamber);
}