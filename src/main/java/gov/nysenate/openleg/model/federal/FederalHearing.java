package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;

/**
 * Represents a federal congressional hearing.
 */
@Entity
@Table(name = "federal_hearings", schema = "master")
public class FederalHearing {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "hearing_id", unique = true, nullable = false)
    private String hearingId;

    @Column(name = "congress", nullable = false)
    private Integer congress;

    @Column(name = "title")
    private String title;

    @Column(name = "hearing_date")
    private LocalDate hearingDate;

    @Column(name = "committee_name")
    private String committeeName;

    @Column(name = "chamber")
    @Enumerated(EnumType.STRING)
    private FederalChamber chamber;

    @Column(name = "hearing_type")
    private String hearingType;

    @Column(name = "location")
    private String location;

    @Column(name = "transcript_text", columnDefinition = "TEXT")
    private String transcriptText;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDate updatedAt;

    // Constructors
    public FederalHearing() {
        this.createdAt = LocalDate.now();
        this.updatedAt = LocalDate.now();
    }

    public FederalHearing(String hearingId, Integer congress, String title) {
        this();
        this.hearingId = hearingId;
        this.congress = congress;
        this.title = title;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getHearingId() { return hearingId; }
    public void setHearingId(String hearingId) { this.hearingId = hearingId; }

    public Integer getCongress() { return congress; }
    public void setCongress(Integer congress) { this.congress = congress; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public LocalDate getHearingDate() { return hearingDate; }
    public void setHearingDate(LocalDate hearingDate) { this.hearingDate = hearingDate; }

    public String getCommitteeName() { return committeeName; }
    public void setCommitteeName(String committeeName) { this.committeeName = committeeName; }

    public FederalChamber getChamber() { return chamber; }
    public void setChamber(FederalChamber chamber) { this.chamber = chamber; }

    public String getHearingType() { return hearingType; }
    public void setHearingType(String hearingType) { this.hearingType = hearingType; }

    public String getLocation() { return location; }
    public void setLocation(String location) { this.location = location; }

    public String getTranscriptText() { return transcriptText; }
    public void setTranscriptText(String transcriptText) { this.transcriptText = transcriptText; }

    public LocalDate getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDate createdAt) { this.createdAt = createdAt; }

    public LocalDate getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDate updatedAt) { this.updatedAt = updatedAt; }

    @Override
    public String toString() {
        return "FederalHearing{" +
                "id=" + id +
                ", hearingId='" + hearingId + '\'' +
                ", congress=" + congress +
                ", title='" + title + '\'' +
                ", hearingDate=" + hearingDate +
                '}';
    }
}