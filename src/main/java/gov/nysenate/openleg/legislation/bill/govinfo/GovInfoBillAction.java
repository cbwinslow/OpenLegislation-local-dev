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
 * Creates an empty GovInfoBillAction with all fields unset (null).
 */
    public GovInfoBillAction() {}

    /**
 * The action date as a string.
 *
 * @return the action date string, or {@code null} if not set
 */
    public String getActionDate() { return actionDate; }
    /**
 * Set the action date using its original string representation.
 *
 * @param actionDate the action date string (original/raw representation as provided by GovInfo)
 */
public void setActionDate(String actionDate) { this.actionDate = actionDate; }

    /**
 * Gets the descriptive text for this bill action.
 *
 * @return the action text, or {@code null} if not set
 */
public String getText() { return text; }
    /**
 * Sets the descriptive text of this bill action.
 *
 * @param text the descriptive text for the action
 */
public void setText(String text) { this.text = text; }

    /**
 * The actor associated with the action (the person or entity performing the action).
 *
 * May contain a member's name and state information suitable for attempting linkage to a member record.
 *
 * @return the actor string, or null if not set
 */
public String getActor() { return actor; }
    /**
 * Set the actor information associated with this bill action.
 *
 * @param actor actor information (for example, a member's name and state used to link the action to a member)
 */
public void setActor(String actor) { this.actor = actor; }

    /**
 * Gets the committee code associated with this action.
 *
 * @return the committee code, or {@code null} if not set
 */
public String getCommitteeCode() { return committeeCode; }
    /**
 * Set the committee code associated with this action.
 *
 * @param committeeCode the committee code to set, or {@code null} to clear it
 */
public void setCommitteeCode(String committeeCode) { this.committeeCode = committeeCode; }

    /**
 * Gets the action date.
 *
 * @return the action date as a {@link java.time.LocalDate}, or {@code null} if not set
 */
public LocalDate getDate() { return date; }
    /**
 * Set the action's date as a LocalDate.
 *
 * @param date the action date parsed into a LocalDate (corresponds to {@code actionDate})
 */
public void setDate(LocalDate date) { this.date = date; }

    /**
     * Determines equality with another object by comparing the actionDate and text fields.
     *
     * @param o the object to compare with
     * @return true if the other object is a GovInfoBillAction with equal actionDate and text, false otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillAction that = (GovInfoBillAction) o;
        return Objects.equals(actionDate, that.actionDate) && Objects.equals(text, that.text);
    }

    /**
     * Computes a hash code for this GovInfoBillAction based on its actionDate and text.
     *
     * @return an int hash code derived from {@code actionDate} and {@code text}
     */
    @Override
    public int hashCode() {
        return Objects.hash(actionDate, text);
    }
}