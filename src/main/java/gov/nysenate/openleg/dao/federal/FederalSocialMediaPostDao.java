package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalSocialMediaPost;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Data access layer for federal social media post operations.
 */
@Repository
public interface FederalSocialMediaPostDao extends JpaRepository<FederalSocialMediaPost, Long> {

    /**
     * Find social media posts by member.
     */
    List<FederalSocialMediaPost> findByMemberIdOrderByPostedAtDesc(Long memberId);

    /**
     * Find social media posts by platform.
     */
    List<FederalSocialMediaPost> findByPlatformOrderByPostedAtDesc(String platform);

    /**
     * Find social media posts by member and platform.
     */
    List<FederalSocialMediaPost> findByMemberIdAndPlatformOrderByPostedAtDesc(Long memberId, String platform);

    /**
     * Find recent social media posts.
     */
    @Query("SELECT p FROM FederalSocialMediaPost p WHERE p.postedAt >= :since " +
           "ORDER BY p.postedAt DESC")
    List<FederalSocialMediaPost> findRecentPosts(@Param("since") LocalDateTime since);

    /**
     * Find social media posts by date range.
     */
    @Query("SELECT p FROM FederalSocialMediaPost p WHERE p.postedAt BETWEEN :startDate AND :endDate " +
           "ORDER BY p.postedAt DESC")
    List<FederalSocialMediaPost> findByPostedAtBetween(
        @Param("startDate") LocalDateTime startDate,
        @Param("endDate") LocalDateTime endDate
    );

    /**
     * Find posts containing specific hashtags.
     */
    @Query("SELECT p FROM FederalSocialMediaPost p WHERE :hashtag = ANY(p.hashtags) " +
           "ORDER BY p.postedAt DESC")
    List<FederalSocialMediaPost> findByHashtag(@Param("hashtag") String hashtag);

    /**
     * Find posts mentioning specific users.
     */
    @Query("SELECT p FROM FederalSocialMediaPost p WHERE :mention = ANY(p.mentions) " +
           "ORDER BY p.postedAt DESC")
    List<FederalSocialMediaPost> findByMention(@Param("mention") String mention);

    /**
     * Get count of posts by platform.
     */
    @Query("SELECT COUNT(p) FROM FederalSocialMediaPost p WHERE p.platform = :platform")
    long countByPlatform(@Param("platform") String platform);

    /**
     * Get count of posts by member.
     */
    @Query("SELECT COUNT(p) FROM FederalSocialMediaPost p WHERE p.member.id = :memberId")
    long countByMember(@Param("memberId") Long memberId);

    /**
     * Find posts with high engagement.
     */
    @Query("SELECT p FROM FederalSocialMediaPost p WHERE " +
           "p.engagementMetrics LIKE '%\"likes\":%' " +
           "ORDER BY p.postedAt DESC")
    List<FederalSocialMediaPost> findHighEngagementPosts(@Param("minLikes") Integer minLikes);
}