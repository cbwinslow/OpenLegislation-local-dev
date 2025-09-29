package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalMember;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Data access layer for federal member operations.
 */
@Repository
public interface FederalMemberDao extends JpaRepository<FederalMember, Long> {

    /**
     * Find a federal member by their bioguide ID.
     */
    Optional<FederalMember> findByBioguideId(String bioguideId);

    /**
     * Find federal members by chamber.
     */
    List<FederalMember> findByChamberOrderByStateAscDistrictAsc(String chamber);

    /**
     * Find current federal members (those currently serving).
     */
    @Query("SELECT m FROM FederalMember m WHERE m.currentMember = true ORDER BY m.state, m.lastName")
    List<FederalMember> findCurrentMembers();

    /**
     * Find federal members by state.
     */
    List<FederalMember> findByStateOrderByLastNameAsc(String state);

    /**
     * Find federal members by party.
     */
    List<FederalMember> findByPartyOrderByStateAscLastNameAsc(String party);

    /**
     * Search federal members by name (case-insensitive partial match).
     */
    @Query("SELECT m FROM FederalMember m WHERE " +
           "LOWER(m.fullName) LIKE LOWER(CONCAT('%', :name, '%')) OR " +
           "LOWER(m.firstName) LIKE LOWER(CONCAT('%', :name, '%')) OR " +
           "LOWER(m.lastName) LIKE LOWER(CONCAT('%', :name, '%')) " +
           "ORDER BY m.lastName, m.firstName")
    List<FederalMember> searchByName(@Param("name") String name);

    /**
     * Get count of current members by chamber.
     */
    @Query("SELECT COUNT(m) FROM FederalMember m WHERE m.currentMember = true AND m.chamber = :chamber")
    long countCurrentMembersByChamber(@Param("chamber") String chamber);

    /**
     * Check if a member exists by bioguide ID.
     */
    boolean existsByBioguideId(String bioguideId);

    /**
     * Find members with social media accounts.
     */
    @Query("SELECT DISTINCT m FROM FederalMember m " +
           "JOIN m.socialMedia sm " +
           "WHERE sm.platform = :platform " +
           "ORDER BY m.state, m.lastName")
    List<FederalMember> findMembersWithSocialMedia(@Param("platform") String platform);
}