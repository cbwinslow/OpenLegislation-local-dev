package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;

/**
 * Represents a federal congressional record transcript.
 */
@Entity
@Table(name = "federal_transcripts", schema = "master")
public class FederalTranscript {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "transcript_id", unique = true, nullable = false)
    private String transcriptId;

    @Column(name = "congress", nullable = false)
    private Integer congress;

    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Column(name = "volume")
    private Integer volume;

    @Column(name = "title")
    private String title;

    @Column(name = "chamber")
    @Enumerated(EnumType.STRING)
    private FederalChamber chamber;

    @Column(name = "transcript_text", columnDefinition = "TEXT")
    private String transcriptText;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDate updatedAt;

    // Constructors
    public FederalTranscript() {
        this.createdAt = LocalDate.now();
        this.updatedAt = LocalDate.now();
    }

    public FederalTranscript(String transcriptId, Integer congress, LocalDate date) {
        this();
        this.transcriptId = transcriptId;
        this.congress = congress;
        this.date = date;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getTranscriptId() { return transcriptId; }
    public void setTranscriptId(String transcriptId) { this.transcriptId = transcriptId; }

    public Integer getCongress() { return congress; }
    public void setCongress(Integer congress) { this.congress = congress; }

    public LocalDate getDate() { return date; }
    public void setDate(LocalDate date) { this.date = date; }

    public Integer getVolume() { return volume; }
    public void setVolume(Integer volume) { this.volume = volume; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public FederalChamber getChamber() { return chamber; }
    public void setChamber(FederalChamber chamber) { this.chamber = chamber; }

    public String getTranscriptText() { return transcriptText; }
    public void setTranscriptText(String transcriptText) { this.transcriptText = transcriptText; }

    public LocalDate getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDate createdAt) { this.createdAt = createdAt; }

    public LocalDate getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDate updatedAt) { this.updatedAt = updatedAt; }

    @Override
    public String toString() {
        return "FederalTranscript{" +
                "id=" + id +
                ", transcriptId='" + transcriptId + '\'' +
                ", congress=" + congress +
                ", date=" + date +
                ", title='" + title + '\'' +
                '}';
    }
}