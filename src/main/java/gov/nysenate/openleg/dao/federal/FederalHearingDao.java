package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalHearing;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

/**
 * Data access layer for federal hearing operations.
 */
@Repository
public interface FederalHearingDao extends JpaRepository<FederalHearing, Long> {

    /**
     * Find a federal hearing by its hearing ID.
     */
    List<FederalHearing> findByHearingId(String hearingId);

    /**
     * Find federal hearings by congress.
     */
    List<FederalHearing> findByCongressOrderByHearingDateDesc(Integer congress);

    /**
     * Find federal hearings by committee.
     */
    List<FederalHearing> findByCommitteeNameOrderByHearingDateDesc(String committeeName);

    /**
     * Find federal hearings by chamber.
     */
    List<FederalHearing> findByChamberOrderByHearingDateDesc(String chamber);

    /**
     * Find federal hearings by date.
     */
    List<FederalHearing> findByHearingDateOrderByTitleAsc(LocalDate hearingDate);

    /**
     * Find federal hearings by date range.
     */
    @Query("SELECT h FROM FederalHearing h WHERE h.hearingDate BETWEEN :startDate AND :endDate " +
           "ORDER BY h.hearingDate DESC")
    List<FederalHearing> findByHearingDateBetween(
        @Param("startDate") LocalDate startDate,
        @Param("endDate") LocalDate endDate
    );

    /**
     * Search federal hearings by title (case-insensitive partial match).
     */
    @Query("SELECT h FROM FederalHearing h WHERE " +
           "LOWER(h.title) LIKE LOWER(CONCAT('%', :title, '%')) " +
           "ORDER BY h.hearingDate DESC")
    List<FederalHearing> searchByTitle(@Param("title") String title);

    /**
     * Get count of hearings by congress.
     */
    @Query("SELECT COUNT(h) FROM FederalHearing h WHERE h.congress = :congress")
    long countByCongress(@Param("congress") Integer congress);

    /**
     * Get count of hearings by committee.
     */
    @Query("SELECT COUNT(h) FROM FederalHearing h WHERE h.committeeName = :committeeName")
    long countByCommittee(@Param("committeeName") String committeeName);
}