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

    /**
 * Constructs a GovInfoDocRef with all fields initialized to null.
 */
    public GovInfoDocRef() {}

    /**
     * Creates a GovInfoDocRef with the specified document type, identifier, URL, and title.
     *
     * @param docType the document type, or null if unknown
     * @param docId the document identifier, or null if unavailable
     * @param url the document URL, or null if not provided
     * @param title the document title, or null if not provided
     */
    public GovInfoDocRef(String docType, String docId, String url, String title) {
        this.docType = docType;
        this.docId = docId;
        this.url = url;
        this.title = title;
    }

    /**
 * Gets the document type.
 *
 * @return the document type string, or {@code null} if not set
 */
    public String getDocType() { return docType; }
    /**
 * Sets the document type for this GovInfoDocRef.
 *
 * @param docType the document type
 */
public void setDocType(String docType) { this.docType = docType; }

    /**
 * Returns the document identifier.
 *
 * @return the document ID string
 */
public String getDocId() { return docId; }
    /**
 * Sets the document identifier.
 *
 * @param docId the document identifier for this document reference
 */
public void setDocId(String docId) { this.docId = docId; }

    /**
 * Gets the document URL.
 *
 * @return the document URL, or null if not set
 */
public String getUrl() { return url; }
    /**
 * Sets the document URL.
 *
 * @param url the URL of the document
 */
public void setUrl(String url) { this.url = url; }

    /**
 * Gets the document title.
 *
 * @return the document title, or null if no title is set
 */
public String getTitle() { return title; }
    /**
 * Sets the document title.
 *
 * @param title the title of the document, or {@code null} to clear it
 */
public void setTitle(String title) { this.title = title; }

    /**
     * Determines whether this GovInfoDocRef is equal to another object by comparing all fields.
     *
     * @param o the object to compare with this instance
     * @return `true` if `o` is a GovInfoDocRef and `docType`, `docId`, `url`, and `title` are equal; `false` otherwise
     */
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

    /**
     * Computes a hash code for this GovInfoDocRef based on its field values.
     *
     * @return the hash code computed from `docType`, `docId`, `url`, and `title`
     */
    @Override
    public int hashCode() {
        return Objects.hash(docType, docId, url, title);
    }

    /**
     * Provide a string representation of this GovInfoDocRef including its field names and values.
     *
     * @return A string containing the class name and field names with their values in the format
     *         "GovInfoDocRef{docType='...', docId='...', url='...', title='...'}".
     */
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