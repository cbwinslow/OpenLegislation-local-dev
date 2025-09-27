package gov.nysenate.openleg.model.db;

import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "bills")
public class DbBill {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "base_bill_id", unique = true, nullable = false)
    private String baseBillId;

    @Column(name = "session_year", nullable = false)
    private int sessionYear;

    private String title;

    @Column(columnDefinition = "TEXT")
    private String summary;

    private String status;

    @Column(columnDefinition = "TEXT")
    private String ldblurb;

    @Column(name = "substituted_by")
    private String substitutedBy;

    @Column(name = "reprint_of")
    private String reprintOf;

    @Column(name = "direct_previous_version")
    private String directPreviousVersion;

    @Column(name = "chapter_num")
    private Integer chapterNum;

    @Column(name = "chapter_year")
    private Integer chapterYear;

    @Column(name = "federal_congress")
    private Integer federalCongress;

    @Column(name = "federal_source")
    private String federalSource;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "summary_vector", columnDefinition = "vector(1536)")
    private float[] summaryVector;

    @ManyToMany(cascade = { CascadeType.PERSIST, CascadeType.MERGE })
    @JoinTable(name = "bill_sponsors",
            joinColumns = @JoinColumn(name = "bill_id"),
            inverseJoinColumns = @JoinColumn(name = "sponsor_id")
    )
    private List<DbSponsor> sponsors = new ArrayList<>();

    @ManyToMany(cascade = { CascadeType.PERSIST, CascadeType.MERGE })
    @JoinTable(name = "bill_committees",
            joinColumns = @JoinColumn(name = "bill_id"),
            inverseJoinColumns = @JoinColumn(name = "committee_id")
    )
    private List<DbCommittee> committees = new ArrayList<>();

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getBaseBillId() {
        return baseBillId;
    }

    public void setBaseBillId(String baseBillId) {
        this.baseBillId = baseBillId;
    }

    public int getSessionYear() {
        return sessionYear;
    }

    public void setSessionYear(int sessionYear) {
        this.sessionYear = sessionYear;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getLdblurb() {
        return ldblurb;
    }

    public void setLdblurb(String ldblurb) {
        this.ldblurb = ldblurb;
    }

    public String getSubstitutedBy() {
        return substitutedBy;
    }

    public void setSubstitutedBy(String substitutedBy) {
        this.substitutedBy = substitutedBy;
    }

    public String getReprintOf() {
        return reprintOf;
    }

    public void setReprintOf(String reprintOf) {
        this.reprintOf = reprintOf;
    }

    public String getDirectPreviousVersion() {
        return directPreviousVersion;
    }

    public void setDirectPreviousVersion(String directPreviousVersion) {
        this.directPreviousVersion = directPreviousVersion;
    }

    public Integer getChapterNum() {
        return chapterNum;
    }

    public void setChapterNum(Integer chapterNum) {
        this.chapterNum = chapterNum;
    }

    public Integer getChapterYear() {
        return chapterYear;
    }

    public void setChapterYear(Integer chapterYear) {
        this.chapterYear = chapterYear;
    }

    public Integer getFederalCongress() {
        return federalCongress;
    }

    public void setFederalCongress(Integer federalCongress) {
        this.federalCongress = federalCongress;
    }

    public String getFederalSource() {
        return federalSource;
    }

    public void setFederalSource(String federalSource) {
        this.federalSource = federalSource;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    public float[] getSummaryVector() {
        return summaryVector;
    }

    public void setSummaryVector(float[] summaryVector) {
        this.summaryVector = summaryVector;
    }

    public List<DbSponsor> getSponsors() {
        return sponsors;
    }

    public void setSponsors(List<DbSponsor> sponsors) {
        this.sponsors = sponsors;
    }

    public List<DbCommittee> getCommittees() {
        return committees;
    }

    public void setCommittees(List<DbCommittee> committees) {
        this.committees = committees;
    }
}