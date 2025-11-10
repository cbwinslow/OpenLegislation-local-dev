package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;

/**
 * Represents a federal committee report.
 */
@Entity
@Table(name = "federal_reports", schema = "master")
public class FederalReport {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "report_id", unique = true, nullable = false)
    private String reportId;

    @Column(name = "congress", nullable = false)
    private Integer congress;

    @Column(name = "report_number")
    private String reportNumber;

    @Column(name = "title")
    private String title;

    @Column(name = "report_type")
    private String reportType;

    @Column(name = "committee_name")
    private String committeeName;

    @Column(name = "chamber")
    @Enumerated(EnumType.STRING)
    private FederalChamber chamber;

    @Column(name = "report_text", columnDefinition = "TEXT")
    private String reportText;

    @Column(name = "report_date")
    private LocalDate reportDate;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDate updatedAt;

    // Constructors
    public FederalReport() {
        this.createdAt = LocalDate.now();
        this.updatedAt = LocalDate.now();
    }

    public FederalReport(String reportId, Integer congress, String title) {
        this();
        this.reportId = reportId;
        this.congress = congress;
        this.title = title;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getReportId() { return reportId; }
    public void setReportId(String reportId) { this.reportId = reportId; }

    public Integer getCongress() { return congress; }
    public void setCongress(Integer congress) { this.congress = congress; }

    public String getReportNumber() { return reportNumber; }
    public void setReportNumber(String reportNumber) { this.reportNumber = reportNumber; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getReportType() { return reportType; }
    public void setReportType(String reportType) { this.reportType = reportType; }

    public String getCommitteeName() { return committeeName; }
    public void setCommitteeName(String committeeName) { this.committeeName = committeeName; }

    public FederalChamber getChamber() { return chamber; }
    public void setChamber(FederalChamber chamber) { this.chamber = chamber; }

    public String getReportText() { return reportText; }
    public void setReportText(String reportText) { this.reportText = reportText; }

    public LocalDate getReportDate() { return reportDate; }
    public void setReportDate(LocalDate reportDate) { this.reportDate = reportDate; }

    public LocalDate getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDate createdAt) { this.createdAt = createdAt; }

    public LocalDate getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDate updatedAt) { this.updatedAt = updatedAt; }

    @Override
    public String toString() {
        return "FederalReport{" +
                "id=" + id +
                ", reportId='" + reportId + '\'' +
                ", congress=" + congress +
                ", title='" + title + '\'' +
                ", committeeName='" + committeeName + '\'' +
                '}';
    }
}