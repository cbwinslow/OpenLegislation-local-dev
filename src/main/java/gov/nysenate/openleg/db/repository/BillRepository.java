package gov.nysenate.openleg.db.repository;

import gov.nysenate.openleg.model.db.DbBill;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface BillRepository extends JpaRepository<DbBill, Long> {

    /**
     * Finds a bill by its base bill ID.
     *
     * @param baseBillId The base bill ID to search for.
     * @return An Optional containing the bill if found, otherwise empty.
     */
    Optional<DbBill> findByBaseBillId(String baseBillId);
}