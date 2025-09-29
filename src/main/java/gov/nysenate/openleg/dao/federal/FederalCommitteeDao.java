package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalCommittee;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Data access layer for federal committee operations.
 */
@Repository
public interface FederalCommitteeDao extends JpaRepository<FederalCommittee, Long> {

    /**
     * Find a federal committee by its code.
     */
    List<FederalCommittee> findByCommitteeCode(String committeeCode);

    /**
     * Find federal committees by chamber.
     */
    List<FederalCommittee> findByChamberOrderByCommitteeNameAsc(String chamber);

    /**
     * Find current federal committees.
     */
    List<FederalCommittee> findByCurrentCommitteeTrueOrderByCommitteeNameAsc();

    /**
     * Find federal committees by type.
     */
    List<FederalCommittee> findByCommitteeTypeOrderByCommitteeNameAsc(String committeeType);

    /**
     * Search federal committees by name (case-insensitive partial match).
     */
    @Query("SELECT c FROM FederalCommittee c WHERE " +
           "LOWER(c.committeeName) LIKE LOWER(CONCAT('%', :name, '%')) " +
           "ORDER BY c.committeeName")
    List<FederalCommittee> searchByName(@Param("name") String name);

    /**
     * Get count of committees by chamber.
     */
    @Query("SELECT COUNT(c) FROM FederalCommittee c WHERE c.chamber = :chamber")
    long countByChamber(@Param("chamber") String chamber);

    /**
     * Get count of current committees by type.
     */
    @Query("SELECT COUNT(c) FROM FederalCommittee c WHERE c.committeeType = :type AND c.currentCommittee = true")
    long countCurrentByType(@Param("type") String type);
}