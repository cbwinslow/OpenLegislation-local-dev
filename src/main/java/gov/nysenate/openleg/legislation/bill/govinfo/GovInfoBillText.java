package gov.nysenate.openleg.legislation.bill.govinfo;

import java.util.Objects;

/**
 * Represents the full text of a GovInfo bill.
 * Parsed from XML <quotedBlock> or similar; no direct member data.
 */
public class GovInfoBillText {
    private String fullText;
    private String summary;

    // Constructors
    public GovInfoBillText() {}

    // Getters/Setters
    public String getFullText() { return fullText; }
    public void setFullText(String fullText) { this.fullText = fullText; }

    public String getSummary() { return summary; }
    public void setSummary(String summary) { this.summary = summary; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillText that = (GovInfoBillText) o;
        return Objects.equals(fullText, that.fullText) && Objects.equals(summary, that.summary);
    }

    @Override
    public int hashCode() {
        return Objects.hash(fullText, summary);
    }
}
