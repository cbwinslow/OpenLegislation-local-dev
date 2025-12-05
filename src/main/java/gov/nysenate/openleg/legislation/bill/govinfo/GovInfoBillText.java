package gov.nysenate.openleg.legislation.bill.govinfo;

import java.util.Objects;

/**
 * Represents the full text of a GovInfo bill.
 * Parsed from XML <quotedBlock> or similar; no direct member data.
 */
public class GovInfoBillText {
    private String fullText;
    private String summary;

    /**
 * Creates an empty GovInfoBillText instance.
 *
 * <p>Initializes the instance with both `fullText` and `summary` set to `null`.</p>
 */
    public GovInfoBillText() {}

    /**
 * Gets the full text of the bill.
 *
 * @return the full bill text, or {@code null} if not set
 */
    public String getFullText() { return fullText; }
    /**
 * Set the full bill text.
 *
 * @param fullText the complete bill text for this bill, or {@code null} if not available
 */
public void setFullText(String fullText) { this.fullText = fullText; }

    /**
 * Gets the summary text associated with the bill.
 *
 * @return the bill summary, or {@code null} if not set.
 */
public String getSummary() { return summary; }
    /**
 * Sets the bill summary text parsed from GovInfo.
 *
 * @param summary the summary text for the bill (may be null)
 */
public void setSummary(String summary) { this.summary = summary; }

    /**
     * Checks whether this GovInfoBillText is equal to another object based on `fullText` and `summary`.
     *
     * @param o the object to compare with this instance
     * @return `true` if `o` is a `GovInfoBillText` and both `fullText` and `summary` are equal, `false` otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillText that = (GovInfoBillText) o;
        return Objects.equals(fullText, that.fullText) && Objects.equals(summary, that.summary);
    }

    /**
     * Computes a hash code for this instance based on the fullText and summary fields.
     *
     * @return an int hash code derived from the fullText and summary
     */
    @Override
    public int hashCode() {
        return Objects.hash(fullText, summary);
    }
}