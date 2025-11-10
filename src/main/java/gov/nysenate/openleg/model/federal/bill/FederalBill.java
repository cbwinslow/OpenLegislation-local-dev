package gov.nysenate.openleg.model.federal.bill;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "federal_bills", schema = "public")
public class FederalBill {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "congress_number", nullable = false)
    private Integer congress;  // e.g., 118

    @Column(name = "bill_type", nullable = false)  // e.g., "hr", "s"
    private String type;

    @Column(name = "number", nullable = false)
    private Integer number;

    @Column(name = "title")
    private String title;

    @Column(name = "summary", columnDefinition = "TEXT")
    private String summary;

    @Column(name = "status")  // e.g., "introduced", "passed"
    private String status;

    @Column(name = "introduced_date")
    private LocalDateTime introducedDate;

    @Column(name = "sponsor_id")
    private String sponsor;  // Link to member

    @Column(name = "text_content", columnDefinition = "TEXT")
    private String fullText;  // Parsed from XML/PDF

    @Column(name = "metadata", columnDefinition = "JSONB")  // Full API response
    private String metadata;

    @Column(name = "source_url", unique = true)
    private String sourceUrl;  // Congress.gov URL for idempotency

    @Column(name = "ingested_at", nullable = false)
    private LocalDateTime ingestedAt = LocalDateTime.now();

    // Constructors
    public FederalBill() {}

    public FederalBill(Integer congress, String type, Integer number, String title, String summary, String status,
                       LocalDateTime introducedDate, String sponsor, String fullText, String metadata,
                       String sourceUrl, LocalDateTime ingestedAt) {
        this.congress = congress;
        this.type = type;
        this.number = number;
        this.title = title;
        this.summary = summary;
        this.status = status;
        this.introducedDate = introducedDate;
        this.sponsor = sponsor;
        this.fullText = fullText;
        this.metadata = metadata;
        this.sourceUrl = sourceUrl;
        this.ingestedAt = ingestedAt;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Integer getCongress() { return congress; }
    public void setCongress(Integer congress) { this.congress = congress; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public Integer getNumber() { return number; }
    public void setNumber(Integer number) { this.number = number; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getSummary() { return summary; }
    public void setSummary(String summary) { this.summary = summary; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public LocalDateTime getIntroducedDate() { return introducedDate; }
    public void setIntroducedDate(LocalDateTime introducedDate) { this.introducedDate = introducedDate; }

    public String getSponsor() { return sponsor; }
    public void setSponsor(String sponsor) { this.sponsor = sponsor; }

    public String getFullText() { return fullText; }
    public void setFullText(String fullText) { this.fullText = fullText; }

    public String getMetadata() { return metadata; }
    public void setMetadata(String metadata) { this.metadata = metadata; }

    public String getSourceUrl() { return sourceUrl; }
    public void setSourceUrl(String sourceUrl) { this.sourceUrl = sourceUrl; }

    public LocalDateTime getIngestedAt() { return ingestedAt; }
    public void setIngestedAt(LocalDateTime ingestedAt) { this.ingestedAt = ingestedAt; }

    @Override
    public String toString() {
        return "FederalBill{" +
                "id=" + id +
                ", congress=" + congress +
                ", type='" + type + '\'' +
                ", number=" + number +
                ", title='" + title + '\'' +
                ", status='" + status + '\'' +
                ", introducedDate=" + introducedDate +
                ", sourceUrl='" + sourceUrl + '\'' +
                ", ingestedAt=" + ingestedAt +
                '}';
    }
}
