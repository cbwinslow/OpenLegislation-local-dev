package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalMemberSocialMedia;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Data access layer for federal member social media operations.
 */
@Repository
public interface FederalMemberSocialMediaDao extends JpaRepository<FederalMemberSocialMedia, Long> {

    /**
     * Find social media accounts by member.
     */
    List<FederalMemberSocialMedia> findByMemberIdOrderByPlatformAsc(Long memberId);

    /**
     * Find social media accounts by platform.
     */
    List<FederalMemberSocialMedia> findByPlatformOrderByLastUpdatedDesc(String platform);

    /**
     * Find verified social media accounts.
     */
    List<FederalMemberSocialMedia> findByVerifiedTrueOrderByPlatformAsc();

    /**
     * Find official social media accounts.
     */
    List<FederalMemberSocialMedia> findByOfficialTrueOrderByPlatformAsc();

    /**
     * Find social media accounts by platform and member.
     */
    List<FederalMemberSocialMedia> findByPlatformAndMemberId(String platform, Long memberId);

    /**
     * Get count of social media accounts by platform.
     */
    @Query("SELECT COUNT(sm) FROM FederalMemberSocialMedia sm WHERE sm.platform = :platform")
    long countByPlatform(@Param("platform") String platform);

    /**
     * Get count of verified accounts by platform.
     */
    @Query("SELECT COUNT(sm) FROM FederalMemberSocialMedia sm WHERE sm.platform = :platform AND sm.verified = true")
    long countVerifiedByPlatform(@Param("platform") String platform);
}