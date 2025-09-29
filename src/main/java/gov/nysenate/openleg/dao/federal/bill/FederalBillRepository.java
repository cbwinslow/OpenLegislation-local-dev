package gov.nysenate.openleg.dao.federal.bill;

import gov.nysenate.openleg.model.federal.bill.FederalBill;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface FederalBillRepository extends JpaRepository<FederalBill, Long> {

    /**
     * Find document by source URL (unique).
     */
    Optional<FederalBill> findBySourceUrl(String sourceUrl);

    /**
     * Check if bill exists by source URL to ensure idempotency.
     */
    boolean existsBySourceUrl(String sourceUrl);

    /**
     * Find bills by congress and type, ordered by number.
     */
    @Query("SELECT b FROM FederalBill b WHERE b.congress = :congress AND b.type = :type ORDER BY b.number")
    List<FederalBill> findByCongressAndType(@Param("congress") Integer congress, @Param("type") String type);

    // Upsert logic can use save() with @Version for optimistic locking if needed
}