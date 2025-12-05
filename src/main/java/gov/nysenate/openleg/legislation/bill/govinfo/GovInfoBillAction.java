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

    /**
 * Creates a new GovInfoBillAction with all fields unset.
 */
    public GovInfoBillAction() {}

    /**
 * The action date as a string.
 *
 * @return the action date string, or {@code null} if not set
 */
    public String getActionDate() { return actionDate; }
    /**
 * Sets the action date string for this GovInfo bill action.
 *
 * @param actionDate the action date string as provided by GovInfo
 */
public void setActionDate(String actionDate) { this.actionDate = actionDate; }

    /**
 * Retrieves the descriptive text of the action.
 *
 * @return the action's descriptive text, or {@code null} if not set
 */
public String getText() { return text; }
    /**
 * Set the action description text.
 *
 * @param text the description of the action
 */
public void setText(String text) { this.text = text; }

    /**
 * The actor associated with this action, typically a member name (and optional state) used for linkage.
 *
 * @return the actor string, or {@code null} if not specified
 */
public String getActor() { return actor; }
    /**
 * Set the actor associated with this action, typically identifying the member or entity responsible.
 *
 * @param actor a string identifying the actor; may include member name and state for linkage or other descriptive text
 */
public void setActor(String actor) { this.actor = actor; }

    /**
 * The committee code associated with this action.
 *
 * @return the committee code, or {@code null} if none is set
 */
public String getCommitteeCode() { return committeeCode; }
    /**
 * Sets the committee code associated with this action.
 *
 * @param committeeCode the committee code (may be null or empty if not applicable)
 */
public void setCommitteeCode(String committeeCode) { this.committeeCode = committeeCode; }

    /**
 * Get the action date as a LocalDate.
 *
 * @return the action date as a LocalDate, or {@code null} if not set
 */
public LocalDate getDate() { return date; }
    /**
 * Sets the action's parsed date.
 *
 * @param date the action date as a LocalDate, or null to clear the stored date
 */
public void setDate(LocalDate date) { this.date = date; }

    /**
     * Determine whether another object is equal to this GovInfoBillAction based on its actionDate and text.
     *
     * @param o the object to compare with this instance
     * @return `true` if `o` is a GovInfoBillAction with equal `actionDate` and `text`, `false` otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillAction that = (GovInfoBillAction) o;
        return Objects.equals(actionDate, that.actionDate) && Objects.equals(text, that.text);
    }

    /**
     * Computes a hash code for this action using its identifying fields.
     *
     * @return an int hash code derived from the {@code actionDate} and {@code text} fields.
     */
    @Override
    public int hashCode() {
        return Objects.hash(actionDate, text);
    }
}