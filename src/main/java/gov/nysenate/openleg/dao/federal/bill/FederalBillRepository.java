package gov.nysenate.openleg.dao.federal.bill;

import gov.nysenate.openleg.model.federal.bill.FederalBill;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Data access layer for federal bill operations.
 */
@Repository
public interface FederalBillRepository extends JpaRepository<FederalBill, Long> {

    /**
     * Find a federal bill by congress, type, and number.
     */
    Optional<FederalBill> findByCongressAndTypeAndNumber(Integer congress, String type, Integer number);

    /**
     * Find federal bills by congress.
     */
    List<FederalBill> findByCongressOrderByTypeAscNumberAsc(Integer congress);

    /**
     * Find federal bills by congress and type.
     */
    List<FederalBill> findByCongressAndTypeOrderByNumberAsc(Integer congress, String type);

    /**
     * Find federal bills by status.
     */
    List<FederalBill> findByStatusOrderByCongressDescIntroducedDateDesc(String status);

    /**
     * Find federal bills by sponsor.
     */
    List<FederalBill> findBySponsorOrderByCongressDescIntroducedDateDesc(String sponsor);

    /**
     * Search federal bills by title (case-insensitive partial match).
     */
    @Query("SELECT b FROM FederalBill b WHERE " +
           "LOWER(b.title) LIKE LOWER(CONCAT('%', :title, '%')) " +
           "ORDER BY b.congress DESC, b.introducedDate DESC")
    List<FederalBill> searchByTitle(@Param("title") String title);

    /**
     * Get count of federal bills by congress.
     */
    @Query("SELECT COUNT(b) FROM FederalBill b WHERE b.congress = :congress")
    long countByCongress(@Param("congress") Integer congress);

    /**
     * Get count of federal bills by status.
     */
    @Query("SELECT COUNT(b) FROM FederalBill b WHERE b.status = :status")
    long countByStatus(@Param("status") String status);

    /**
     * Check if a federal bill exists by source URL.
     */
    boolean existsBySourceUrl(String sourceUrl);

    /**
     * Find federal bills by source.
     */
    List<FederalBill> findBySourceUrlIn(List<String> sourceUrls);

    /**
     * Get recent federal bills (last 30 days).
     */
    @Query("SELECT b FROM FederalBill b WHERE b.introducedDate >= CURRENT_DATE - 30 " +
           "ORDER BY b.introducedDate DESC")
    List<FederalBill> findRecentBills();

    /**
     * Get federal bills by date range.
     */
    @Query("SELECT b FROM FederalBill b WHERE b.introducedDate BETWEEN :startDate AND :endDate " +
           "ORDER BY b.introducedDate DESC")
    List<FederalBill> findByIntroducedDateBetween(
        @Param("startDate") java.time.LocalDateTime startDate,
        @Param("endDate") java.time.LocalDateTime endDate
    );
}