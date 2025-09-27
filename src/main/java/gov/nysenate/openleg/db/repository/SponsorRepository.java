package gov.nysenate.openleg.db.repository;

import gov.nysenate.openleg.model.db.DbSponsor;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface SponsorRepository extends JpaRepository<DbSponsor, Long> {

    /**
     * Finds a sponsor by their member ID.
     *
     * @param memberId The member ID to search for.
     * @return An Optional containing the sponsor if found, otherwise empty.
     */
    Optional<DbSponsor> findByMemberId(String memberId);
}