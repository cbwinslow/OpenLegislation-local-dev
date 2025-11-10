package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;

/**
 * Represents a Code of Federal Regulations section.
 */
@Entity
@Table(name = "federal_cfr", schema = "master")
public class FederalCFR {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "title", nullable = false)
    private Integer title;

    @Column(name = "part", nullable = false)
    private Integer part;

    @Column(name = "section")
    private String section;

    @Column(name = "title_text")
    private String titleText;

    @Column(name = "part_text")
    private String partText;

    @Column(name = "section_text", columnDefinition = "TEXT")
    private String sectionText;

    @Column(name = "effective_date")
    private LocalDate effectiveDate;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDate updatedAt;

    // Constructors
    public FederalCFR() {
        this.createdAt = LocalDate.now();
        this.updatedAt = LocalDate.now();
    }

    public FederalCFR(Integer title, Integer part, String section) {
        this();
        this.title = title;
        this.part = part;
        this.section = section;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Integer getTitle() { return title; }
    public void setTitle(Integer title) { this.title = title; }

    public Integer getPart() { return part; }
    public void setPart(Integer part) { this.part = part; }

    public String getSection() { return section; }
    public void setSection(String section) { this.section = section; }

    public String getTitleText() { return titleText; }
    public void setTitleText(String titleText) { this.titleText = titleText; }

    public String getPartText() { return partText; }
    public void setPartText(String partText) { this.partText = partText; }

    public String getSectionText() { return sectionText; }
    public void setSectionText(String sectionText) { this.sectionText = sectionText; }

    public LocalDate getEffectiveDate() { return effectiveDate; }
    public void setEffectiveDate(LocalDate effectiveDate) { this.effectiveDate = effectiveDate; }

    public LocalDate getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDate createdAt) { this.createdAt = createdAt; }

    public LocalDate getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDate updatedAt) { this.updatedAt = updatedAt; }

    @Override
    public String toString() {
        return "FederalCFR{" +
                "id=" + id +
                ", title=" + title +
                ", part=" + part +
                ", section='" + section + '\'' +
                ", effectiveDate=" + effectiveDate +
                '}';
    }
}