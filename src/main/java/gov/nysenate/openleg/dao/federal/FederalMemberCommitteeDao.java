package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalMemberCommittee;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Data access layer for federal member committee operations.
 */
@Repository
public interface FederalMemberCommitteeDao extends JpaRepository<FederalMemberCommittee, Long> {

    /**
     * Find committee assignments by member.
     */
    List<FederalMemberCommittee> findByMemberIdOrderByStartDateDesc(Long memberId);

    /**
     * Find committee assignments by committee name.
     */
    List<FederalMemberCommittee> findByCommitteeNameOrderByStartDateDesc(String committeeName);

    /**
     * Find current committee assignments for a member.
     */
    @Query("SELECT cm FROM FederalMemberCommittee cm WHERE cm.member.id = :memberId " +
           "AND (cm.endDate IS NULL OR cm.endDate >= CURRENT_DATE) " +
           "ORDER BY cm.startDate DESC")
    List<FederalMemberCommittee> findCurrentAssignmentsByMember(@Param("memberId") Long memberId);

    /**
     * Find committee members by role.
     */
    List<FederalMemberCommittee> findByRoleAndChamberOrderByCommitteeNameAsc(String role, String chamber);

    /**
     * Get count of committee assignments by chamber.
     */
    @Query("SELECT COUNT(cm) FROM FederalMemberCommittee cm WHERE cm.chamber = :chamber")
    long countByChamber(@Param("chamber") String chamber);
}