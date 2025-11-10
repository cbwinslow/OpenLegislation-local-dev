package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;

/**
 * Represents a federal register document.
 */
@Entity
@Table(name = "federal_register", schema = "master")
public class FederalRegister {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "document_number", unique = true, nullable = false)
    private String documentNumber;

    @Column(name = "publication_date", nullable = false)
    private LocalDate publicationDate;

    @Column(name = "title")
    private String title;

    @Column(name = "agency")
    private String agency;

    @Column(name = "document_type")
    private String documentType;

    @Column(name = "abstract_text", columnDefinition = "TEXT")
    private String abstractText;

    @Column(name = "full_text", columnDefinition = "TEXT")
    private String fullText;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDate updatedAt;

    // Constructors
    public FederalRegister() {
        this.createdAt = LocalDate.now();
        this.updatedAt = LocalDate.now();
    }

    public FederalRegister(String documentNumber, LocalDate publicationDate, String title) {
        this();
        this.documentNumber = documentNumber;
        this.publicationDate = publicationDate;
        this.title = title;
    }

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getDocumentNumber() { return documentNumber; }
    public void setDocumentNumber(String documentNumber) { this.documentNumber = documentNumber; }

    public LocalDate getPublicationDate() { return publicationDate; }
    public void setPublicationDate(LocalDate publicationDate) { this.publicationDate = publicationDate; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getAgency() { return agency; }
    public void setAgency(String agency) { this.agency = agency; }

    public String getDocumentType() { return documentType; }
    public void setDocumentType(String documentType) { this.documentType = documentType; }

    public String getAbstractText() { return abstractText; }
    public void setAbstractText(String abstractText) { this.abstractText = abstractText; }

    public String getFullText() { return fullText; }
    public void setFullText(String fullText) { this.fullText = fullText; }

    public LocalDate getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDate createdAt) { this.createdAt = createdAt; }

    public LocalDate getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDate updatedAt) { this.updatedAt = updatedAt; }

    @Override
    public String toString() {
        return "FederalRegister{" +
                "id=" + id +
                ", documentNumber='" + documentNumber + '\'' +
                ", publicationDate=" + publicationDate +
                ", title='" + title + '\'' +
                ", agency='" + agency + '\'' +
                '}';
    }
}