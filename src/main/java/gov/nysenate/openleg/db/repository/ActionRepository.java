package gov.nysenate.openleg.db.repository;

import gov.nysenate.openleg.model.db.DbAction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ActionRepository extends JpaRepository<DbAction, Long> {

    /**
     * Finds all actions for a given bill ID.
     *
     * @param billId The ID of the bill to find actions for.
     * @return A list of actions for the given bill.
     */
    List<DbAction> findByBillId(Long billId);
}