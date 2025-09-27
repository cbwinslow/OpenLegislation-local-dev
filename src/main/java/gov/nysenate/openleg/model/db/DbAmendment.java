package gov.nysenate.openleg.model.db;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "amendments")
public class DbAmendment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "bill_id")
    private DbBill bill;

    private String version;

    @Column(columnDefinition = "TEXT")
    private String memo;

    @Column(name = "law_section")
    private String lawSection;

    @Column(name = "law_code")
    private String lawCode;

    @Column(name = "act_clause", columnDefinition = "TEXT")
    private String actClause;

    @Column(name = "full_text", columnDefinition = "TEXT")
    private String fullText;

    private boolean stricken;

    @Column(name = "uni_bill")
    private boolean uniBill;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "text_vector", columnDefinition = "vector(1536)")
    private float[] textVector;

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public DbBill getBill() {
        return bill;
    }

    public void setBill(DbBill bill) {
        this.bill = bill;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getMemo() {
        return memo;
    }

    public void setMemo(String memo) {
        this.memo = memo;
    }

    public String getLawSection() {
        return lawSection;
    }

    public void setLawSection(String lawSection) {
        this.lawSection = lawSection;
    }

    public String getLawCode() {
        return lawCode;
    }

    public void setLawCode(String lawCode) {
        this.lawCode = lawCode;
    }

    public String getActClause() {
        return actClause;
    }

    public void setActClause(String actClause) {
        this.actClause = actClause;
    }

    public String getFullText() {
        return fullText;
    }

    public void setFullText(String fullText) {
        this.fullText = fullText;
    }

    public boolean isStricken() {
        return stricken;
    }

    public void setStricken(boolean stricken) {
        this.stricken = stricken;
    }

    public boolean isUniBill() {
        return uniBill;
    }

    public void setUniBill(boolean uniBill) {
        this.uniBill = uniBill;
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

    public float[] getTextVector() {
        return textVector;
    }

    public void setTextVector(float[] textVector) {
        this.textVector = textVector;
    }
}