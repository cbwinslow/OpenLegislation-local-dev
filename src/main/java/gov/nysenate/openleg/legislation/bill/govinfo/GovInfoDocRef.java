package gov.nysenate.openleg.legislation.bill.govinfo;

import java.util.Objects;

/**
 * Represents a document reference in a GovInfo bill.
 * Parsed from XML document reference elements.
 */
public class GovInfoDocRef {
    private String docType;
    private String docId;
    private String url;
    private String title;

    // Constructors
    public GovInfoDocRef() {}

    public GovInfoDocRef(String docType, String docId, String url, String title) {
        this.docType = docType;
        this.docId = docId;
        this.url = url;
        this.title = title;
    }

    // Getters/Setters
    public String getDocType() { return docType; }
    public void setDocType(String docType) { this.docType = docType; }

    public String getDocId() { return docId; }
    public void setDocId(String docId) { this.docId = docId; }

    public String getUrl() { return url; }
    public void setUrl(String url) { this.url = url; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoDocRef that = (GovInfoDocRef) o;
        return Objects.equals(docType, that.docType) &&
               Objects.equals(docId, that.docId) &&
               Objects.equals(url, that.url) &&
               Objects.equals(title, that.title);
    }

    @Override
    public int hashCode() {
        return Objects.hash(docType, docId, url, title);
    }

    @Override
    public String toString() {
        return "GovInfoDocRef{" +
                "docType='" + docType + '\'' +
                ", docId='" + docId + '\'' +
                ", url='" + url + '\'' +
                ", title='" + title + '\'' +
                '}';
    }
}