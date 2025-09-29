 package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Represents a social media post from a federal legislator.
 */
@Entity
@Table(name = "federal_social_media_posts", schema = "master")
public class FederalSocialMediaPost {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "social_media_id", nullable = false)
    private FederalMemberSocialMedia socialMedia;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id", nullable = false)
    private FederalMember member;

    @Column(name = "platform", nullable = false)
    private String platform;

    @Column(name = "post_id", nullable = false)
    private String postId;

    @Column(name = "content", columnDefinition = "TEXT")
    private String content;

    @Column(name = "posted_at", nullable = false)
    private LocalDateTime postedAt;

    @Column(name = "url")
    private String url;

    @Column(name = "engagement_metrics", columnDefinition = "JSONB")
    private String engagementMetrics;

    @Column(name = "kg_entities", columnDefinition = "JSONB")
    private String kgEntities;

    @Column(name = "hashtags", columnDefinition = "TEXT[]")
    private String[] hashtags;

    @Column(name = "mentions", columnDefinition = "TEXT[]")
    private String[] mentions;

    @Column(name = "media_urls", columnDefinition = "TEXT[]")
    private String[] mediaUrls;

    @Column(name = "is_reply", nullable = false)
    private Boolean isReply = false;

    @Column(name = "reply_to_id")
    private String replyToId;

    @Column(name = "is_retweet", nullable = false)
    private Boolean isRetweet = false;

    @Column(name = "retweet_of_id")
    private String retweetOfId;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    // Constructors
    public FederalSocialMediaPost() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public FederalMemberSocialMedia getSocialMedia() { return socialMedia; }
    public void setSocialMedia(FederalMemberSocialMedia socialMedia) { this.socialMedia = socialMedia; }

    public FederalMember getMember() { return member; }
    public void setMember(FederalMember member) { this.member = member; }

    public String getPlatform() { return platform; }
    public void setPlatform(String platform) { this.platform = platform; }

    public String getPostId() { return postId; }
    public void setPostId(String postId) { this.postId = postId; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public LocalDateTime getPostedAt() { return postedAt; }
    public void setPostedAt(LocalDateTime postedAt) { this.postedAt = postedAt; }

    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }

    public String getEngagementMetrics() { return engagementMetrics; }
    public void setEngagementMetrics(String engagementMetrics) { this.engagementMetrics = engagementMetrics; }

    public String getKgEntities() { return kgEntities; }
    public void setKgEntities(String kgEntities) { this.kgEntities = kgEntities; }

    public String[] getHashtags() { return hashtags; }
    public void setHashtags(String[] hashtags) { this.hashtags = hashtags; }

    public String[] getMentions() { return mentions; }
    public void setMentions(String[] mentions) { this.mentions = mentions; }

    public String[] getMediaUrls() { return mediaUrls; }
    public void setMediaUrls(String[] mediaUrls) { this.mediaUrls = mediaUrls; }

    public Boolean getIsReply() { return isReply; }
    public void setIsReply(Boolean isReply) { this.isReply = isReply; }

    public String getReplyToId() { return replyToId; }
    public void setReplyToId(String replyToId) { this.replyToId = replyToId; }

    public Boolean getIsRetweet() { return isRetweet; }
    public void setIsRetweet(Boolean isRetweet) { this.isRetweet = isRetweet; }

    public String getRetweetOfId() { return retweetOfId; }
    public void setRetweetOfId(String retweetOfId) { this.retweetOfId = retweetOfId; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }

    @Override
    public String toString() {
        return "FederalSocialMediaPost{" +
                "id=" + id +
                ", platform='" + platform + '\'' +
                ", postId='" + postId + '\'' +
                ", postedAt=" + postedAt +
                ", content='" + (content != null ? content.substring(0, Math.min(content.length(), 50)) : "") + "..." + '\'' +
                '}';
    }
}