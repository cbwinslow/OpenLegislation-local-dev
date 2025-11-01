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
 * Creates an empty GovInfoDocRef with all fields unset.
 */
    public GovInfoDocRef() {}

    /**
     * Create a GovInfoDocRef with the specified document type, identifier, URL, and title.
     *
     * @param docType the type of the referenced document (e.g., "bill", "summary")
     * @param docId   the identifier of the document as provided by GovInfo
     * @param url     the web address where the document can be accessed
     * @param title   the title or brief description of the document
     */
    public GovInfoDocRef(String docType, String docId, String url, String title) {
        this.docType = docType;
        this.docId = docId;
        this.url = url;
        this.title = title;
    }

    /**
 * Gets the type of the referenced GovInfo document.
 *
 * @return the document type, or {@code null} if not set
 */
    public String getDocType() { return docType; }
    /**
 * Set the document type for this reference.
 *
 * @param docType the document type identifier (e.g., a descriptor such as "amendment", "text", or other GovInfo document type)
 */
public void setDocType(String docType) { this.docType = docType; }

    /**
 * Gets the document identifier.
 *
 * @return the document identifier, or {@code null} if not set
 */
public String getDocId() { return docId; }
    /**
 * Sets the document identifier for this GovInfoDocRef.
 *
 * @param docId the identifier of the document
 */
public void setDocId(String docId) { this.docId = docId; }

    /**
 * Gets the URL of the referenced GovInfo document.
 *
 * @return the document URL, or {@code null} if not set
 */
public String getUrl() { return url; }
    /**
 * Set the URL of the document.
 *
 * @param url the URL to the document
 */
public void setUrl(String url) { this.url = url; }

    /**
 * Gets the title of the document reference.
 *
 * @return the document's title, or null if not set
 */
public String getTitle() { return title; }
    /**
 * Sets the title of the document reference.
 *
 * @param title the document title, may be null
 */
public void setTitle(String title) { this.title = title; }

    /**
     * Determines whether the specified object is equal to this GovInfoDocRef.
     *
     * @param o the object to compare with this instance
     * @return `true` if `o` is a GovInfoDocRef and its `docType`, `docId`, `url`, and `title` are equal to this instance's corresponding fields, `false` otherwise
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
     * Compute a hash code for this GovInfoDocRef based on its identifying fields.
     *
     * @return a hash code derived from docType, docId, url, and title
     */
    @Override
    public int hashCode() {
        return Objects.hash(docType, docId, url, title);
    }

    /**
     * Produce a string representation of this GovInfoDocRef containing its field values.
     *
     * @return a string in the format GovInfoDocRef{docType='...', docId='...', url='...', title='...'}
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