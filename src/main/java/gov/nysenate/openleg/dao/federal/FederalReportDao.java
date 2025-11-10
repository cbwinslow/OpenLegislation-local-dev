package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalReport;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Data access layer for federal report operations.
 */
@Repository
public interface FederalReportDao extends JpaRepository<FederalReport, Long> {

    /**
     * Find a federal report by its report ID.
     */
    List<FederalReport> findByReportId(String reportId);

    /**
     * Find federal reports by congress.
     */
    List<FederalReport> findByCongressOrderByReportDateDesc(Integer congress);

    /**
     * Find federal reports by committee.
     */
    List<FederalReport> findByCommitteeNameOrderByReportDateDesc(String committeeName);

    /**
     * Find federal reports by chamber.
     */
    List<FederalReport> findByChamberOrderByReportDateDesc(String chamber);

    /**
     * Find federal reports by report type.
     */
    List<FederalReport> findByReportTypeOrderByReportDateDesc(String reportType);

    /**
     * Search federal reports by title (case-insensitive partial match).
     */
    @Query("SELECT r FROM FederalReport r WHERE " +
           "LOWER(r.title) LIKE LOWER(CONCAT('%', :title, '%')) " +
           "ORDER BY r.reportDate DESC")
    List<FederalReport> searchByTitle(@Param("title") String title);

    /**
     * Get count of reports by congress.
     */
    @Query("SELECT COUNT(r) FROM FederalReport r WHERE r.congress = :congress")
    long countByCongress(@Param("congress") Integer congress);

    /**
     * Get count of reports by committee.
     */
    @Query("SELECT COUNT(r) FROM FederalReport r WHERE r.committeeName = :committeeName")
    long countByCommittee(@Param("committeeName") String committeeName);
}