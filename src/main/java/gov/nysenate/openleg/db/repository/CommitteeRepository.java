package gov.nysenate.openleg.db.repository;

import gov.nysenate.openleg.model.db.DbCommittee;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CommitteeRepository extends JpaRepository<DbCommittee, Long> {

    /**
     * Finds a committee by its committee ID.
     *
     * @param committeeId The committee ID to search for.
     * @return An Optional containing the committee if found, otherwise empty.
     */
    Optional<DbCommittee> findByCommitteeId(String committeeId);
}