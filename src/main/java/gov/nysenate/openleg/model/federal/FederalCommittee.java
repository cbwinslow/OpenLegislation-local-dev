package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;

/**
 * Represents a federal committee or subcommittee.
 */
@Entity
@Table(name = "federal_committees", schema = "master")
public class FederalCommittee {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "committee_code", unique = true, nullable = false)
    private String committeeCode;

    @Column(name = "committee_name", nullable = false)
    private String committeeName;

    @Column(name = "full_name")
    private String fullName;

    @Column(name = "chamber", nullable = false)
    @Enumerated(EnumType.STRING)
    private FederalChamber chamber;

    @Column(name = "committee_type")
    private String committeeType; // standing, select, joint, etc.

    @Column(name = "jurisdiction", columnDefinition = "TEXT")
    private String jurisdiction;

    @Column(name = "established_date")
    private LocalDate establishedDate;

    @Column(name = "dissolved_date")
    private LocalDate dissolvedDate;

    @Column(name = "current_committee", nullable = false)
    private Boolean currentCommittee = true;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDate updatedAt;

    // Constructors
    public FederalCommittee() {
        this.createdAt = LocalDate.now();
        this.updatedAt = LocalDate.now();
    }

    public FederalCommittee(String committeeCode, String committeeName, FederalChamber chamber) {
        this();
        this.committeeCode = committeeCode;
        this.committeeName = committeeName;
        this.chamber = chamber;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getCommitteeCode() { return committeeCode; }
    public void setCommitteeCode(String committeeCode) { this.committeeCode = committeeCode; }

    public String getCommitteeName() { return committeeName; }
    public void setCommitteeName(String committeeName) { this.committeeName = committeeName; }

    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }

    public FederalChamber getChamber() { return chamber; }
    public void setChamber(FederalChamber chamber) { this.chamber = chamber; }

    public String getCommitteeType() { return committeeType; }
    public void setCommitteeType(String committeeType) { this.committeeType = committeeType; }

    public String getJurisdiction() { return jurisdiction; }
    public void setJurisdiction(String jurisdiction) { this.jurisdiction = jurisdiction; }

    public LocalDate getEstablishedDate() { return establishedDate; }
    public void setEstablishedDate(LocalDate establishedDate) { this.establishedDate = establishedDate; }

    public LocalDate getDissolvedDate() { return dissolvedDate; }
    public void setDissolvedDate(LocalDate dissolvedDate) { this.dissolvedDate = dissolvedDate; }

    public Boolean getCurrentCommittee() { return currentCommittee; }
    public void setCurrentCommittee(Boolean currentCommittee) { this.currentCommittee = currentCommittee; }

    public LocalDate getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDate createdAt) { this.createdAt = createdAt; }

    public LocalDate getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDate updatedAt) { this.updatedAt = updatedAt; }

    @Override
    public String toString() {
        return "FederalCommittee{" +
                "id=" + id +
                ", committeeCode='" + committeeCode + '\'' +
                ", committeeName='" + committeeName + '\'' +
                ", chamber=" + chamber +
                ", committeeType='" + committeeType + '\'' +
                ", currentCommittee=" + currentCommittee +
                '}';
    }
}