package gov.nysenate.openleg.model.document;

import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(name = "documents")
public class Document {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "source", nullable = false)
    private String source;  // e.g., "wikileaks", "cdc"

    @Column(name = "url", nullable = false)
    private String url;

    @Column(name = "title")
    private String title;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Column(name = "pub_date")
    private LocalDateTime pubDate;

    @Column(name = "content", columnDefinition = "TEXT")
    private String content;  // Extracted text

    @Column(name = "metadata", columnDefinition = "JSONB")
    private String metadata;  // JSON string for flexible fields

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    // Constructors
    public Document() {}

    public Document(String source, String url, String title, String description, LocalDateTime pubDate, String content, String metadata) {
        this.source = source;
        this.url = url;
        this.title = title;
        this.description = description;
        this.pubDate = pubDate;
        this.content = content;
        this.metadata = metadata;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }

    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public LocalDateTime getPubDate() { return pubDate; }
    public void setPubDate(LocalDateTime pubDate) { this.pubDate = pubDate; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public String getMetadata() { return metadata; }
    public void setMetadata(String metadata) { this.metadata = metadata; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    @Override
    public String toString() {
        return "Document{" +
                "id=" + id +
                ", source='" + source + '\'' +
                ", url='" + url + '\'' +
                ", title='" + title + '\'' +
                ", pubDate=" + pubDate +
                ", createdAt=" + createdAt +
                '}';
    }
}
