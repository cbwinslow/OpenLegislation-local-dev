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
 * Creates a new GovInfoBillText with no full text or summary set.
 */
    public GovInfoBillText() {}

    /**
 * Gets the full bill text parsed from GovInfo.
 *
 * @return the full bill text, or {@code null} if not set
 */
    public String getFullText() { return fullText; }
    /**
 * Sets the full text of the bill as parsed from GovInfo XML.
 *
 * @param fullText the bill's full text (may be null)
 */
public void setFullText(String fullText) { this.fullText = fullText; }

    /**
 * The bill's summary text.
 *
 * @return the bill summary, or null if not set
 */
public String getSummary() { return summary; }
    /**
 * Sets the bill summary text.
 *
 * @param summary the bill summary text, or null to clear the summary
 */
public void setSummary(String summary) { this.summary = summary; }

    /**
     * Determine whether this GovInfoBillText is equal to another object.
     *
     * Two GovInfoBillText instances are equal when their `fullText` and `summary` fields are both equal.
     *
     * @param o the object to compare with
     * @return `true` if the given object is a GovInfoBillText with equal `fullText` and `summary`, `false` otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillText that = (GovInfoBillText) o;
        return Objects.equals(fullText, that.fullText) && Objects.equals(summary, that.summary);
    }

    /**
     * Computes a hash code for this GovInfoBillText based on its stored text and summary.
     *
     * @return an int hash code derived from the `fullText` and `summary` fields
     */
    @Override
    public int hashCode() {
        return Objects.hash(fullText, summary);
    }
}