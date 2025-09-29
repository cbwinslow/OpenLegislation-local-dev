package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;
import java.util.Objects;

/**
 * Represents a social media account for a federal legislator.
 */
@Entity
@Table(name = "federal_member_social_media", schema = "master",
       uniqueConstraints = @UniqueConstraint(columnNames = {"member_id", "platform"}))
public class FederalMemberSocialMedia {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id", nullable = false)
    private FederalMember member;

    @Column(name = "platform", nullable = false, length = 20)
    private String platform; // twitter, facebook, youtube, instagram, etc.

    @Column(name = "handle")
    private String handle; // username or page name

    @Column(name = "url")
    private String url; // full URL to the profile

    @Column(name = "follower_count")
    private Integer followerCount;

    @Column(name = "following_count")
    private Integer followingCount;

    @Column(name = "is_verified", nullable = false)
    private boolean verified = false;

    @Column(name = "is_official", nullable = false)
    private boolean official = true;

    @Column(name = "last_updated")
    private LocalDate lastUpdated;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    // Constructors
    public FederalMemberSocialMedia() {
        this.createdAt = LocalDate.now();
        this.lastUpdated = LocalDate.now();
    }

    public FederalMemberSocialMedia(FederalMember member, String platform, String handle, String url) {
        this();
        this.member = member;
        this.platform = platform;
        this.handle = handle;
        this.url = url;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public FederalMember getMember() {
        return member;
    }

    public void setMember(FederalMember member) {
        this.member = member;
    }

    public String getPlatform() {
        return platform;
    }

    public void setPlatform(String platform) {
        this.platform = platform;
    }

    public String getHandle() {
        return handle;
    }

    public void setHandle(String handle) {
        this.handle = handle;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public Integer getFollowerCount() {
        return followerCount;
    }

    public void setFollowerCount(Integer followerCount) {
        this.followerCount = followerCount;
    }

    public Integer getFollowingCount() {
        return followingCount;
    }

    public void setFollowingCount(Integer followingCount) {
        this.followingCount = followingCount;
    }

    public boolean isVerified() {
        return verified;
    }

    public void setVerified(boolean verified) {
        this.verified = verified;
    }

    public boolean isOfficial() {
        return official;
    }

    public void setOfficial(boolean official) {
        this.official = official;
    }

    public LocalDate getLastUpdated() {
        return lastUpdated;
    }

    public void setLastUpdated(LocalDate lastUpdated) {
        this.lastUpdated = lastUpdated;
    }

    public LocalDate getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDate createdAt) {
        this.createdAt = createdAt;
    }

    // Business methods
    public void updateCounts(Integer followers, Integer following) {
        this.followerCount = followers;
        this.followingCount = following;
        this.lastUpdated = LocalDate.now();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        FederalMemberSocialMedia that = (FederalMemberSocialMedia) o;
        return Objects.equals(member, that.member) &&
               Objects.equals(platform, that.platform);
    }

    @Override
    public int hashCode() {
        return Objects.hash(member, platform);
    }

    @Override
    public String toString() {
        return "FederalMemberSocialMedia{" +
                "id=" + id +
                ", member=" + (member != null ? member.getBioguideId() : "null") +
                ", platform='" + platform + '\'' +
                ", handle='" + handle + '\'' +
                ", url='" + url + '\'' +
                ", followerCount=" + followerCount +
                ", verified=" + verified +
                ", official=" + official +
                '}';
    }
}