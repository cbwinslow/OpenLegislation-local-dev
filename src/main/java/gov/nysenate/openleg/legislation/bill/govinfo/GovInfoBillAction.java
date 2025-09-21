package gov.nysenate.openleg.legislation.bill.govinfo;

import java.time.LocalDate;
import java.util.Objects;

/**
 * Represents an action on a GovInfo bill (e.g., introduction, committee referral).
 * Parsed from XML <action> elements; may link to member if actor specified.
 */
public class GovInfoBillAction {
    private String actionDate;
    private String text;
    private String actor; // May contain member name/state for linkage
    private String committeeCode;
    private LocalDate date;

    // Constructors
    public GovInfoBillAction() {}

    // Getters/Setters
    public String getActionDate() { return actionDate; }
    public void setActionDate(String actionDate) { this.actionDate = actionDate; }

    public String getText() { return text; }
    public void setText(String text) { this.text = text; }

    public String getActor() { return actor; }
    public void setActor(String actor) { this.actor = actor; }

    public String getCommitteeCode() { return committeeCode; }
    public void setCommitteeCode(String committeeCode) { this.committeeCode = committeeCode; }

    public LocalDate getDate() { return date; }
    public void setDate(LocalDate date) { this.date = date; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillAction that = (GovInfoBillAction) o;
        return Objects.equals(actionDate, that.actionDate) && Objects.equals(text, that.text);
    }

    @Override
    public int hashCode() {
        return Objects.hash(actionDate, text);
    }
}
