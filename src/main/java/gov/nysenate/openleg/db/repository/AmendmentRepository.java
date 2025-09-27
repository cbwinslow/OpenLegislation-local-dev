package gov.nysenate.openleg.db.repository;

import gov.nysenate.openleg.model.db.DbAmendment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AmendmentRepository extends JpaRepository<DbAmendment, Long> {

    /**
     * Finds all amendments for a given bill ID.
     *
     * @param billId The ID of the bill to find amendments for.
     * @return A list of amendments for the given bill.
     */
    List<DbAmendment> findByBillId(Long billId);
}