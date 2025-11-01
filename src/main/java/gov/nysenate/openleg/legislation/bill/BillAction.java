package gov.nysenate.openleg.legislation.bill;

import com.google.common.collect.ComparisonChain;
import gov.nysenate.openleg.legislation.committee.Chamber;
import org.apache.commons.lang3.StringUtils;

import java.io.Serial;
import java.io.Serializable;
import java.time.LocalDate;
import java.util.Comparator;
import java.util.Objects;

/**
 * Represents a single action on a single bill. E.g. REFERRED TO RULES.
 */
public class BillAction implements Serializable, Comparable<BillAction>
{
    @Serial
    private static final long serialVersionUID = -508975280380827827L;

    /** Identifies the bill this action was taken on. */
    private BillId billId;

    /** The date this action was performed. Has no time component. */
    private LocalDate date;

    /** The chamber in which this action occurred */
    private Chamber chamber;

    /** Number used for chronological ordering. */
    private int sequenceNo = 0;

    /** The text of this action. */
    private String text = "";

    /** The type of the action (e.g., federal, state, etc.) */
    private String type;

    /**
     * Creates an empty BillAction instance with default field values.
     */

    public BillAction() {
        super();
    }

    /**
     * Create a BillAction with the specified date, text, chamber, sequence number, bill id, and type.
     *
     * @param date the date of the action
     * @param text the action description
     * @param chamber the chamber where the action occurred
     * @param sequenceNo ordering index for the action (lower values occur earlier)
     * @param billId the identifier of the bill this action pertains to
     * @param type the action type
     */
    public BillAction(LocalDate date, String text, Chamber chamber, int sequenceNo, BillId billId, String type) {
        super();
        this.setDate(date);
        this.setText(text);
        this.setBillId(billId);
        this.setChamber(chamber);
        this.setSequenceNo(sequenceNo);
        this.setType(type);
    }

    /** --- Overrides --- */

    @Override
    public String toString() {
        return date.toString() + " (" + chamber + ") " + text;
    }

    /**
     * Every BillAction is assigned a BillId which may contain an amendment version other than
     * the base version. For the sake of equality checking, we will use the base version of the
     * bill id since the actions are stored on the base bill anyways.
     */
    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null || getClass() != obj.getClass()) return false;
        final BillAction other = (BillAction) obj;
        return this.billId.equalsBase(other.billId) &&
               Objects.equals(this.date, other.date) &&
               Objects.equals(this.sequenceNo, other.sequenceNo) &&
               Objects.equals(this.chamber, other.chamber) &&
               StringUtils.equalsIgnoreCase(this.text, other.text);
    }

    @Override
    public int hashCode() {
        return 31 * billId.hashCodeBase() + Objects.hash(date, sequenceNo, chamber, text.toLowerCase());
    }

    @Override
    public int compareTo(BillAction o) {
        return ComparisonChain.start().compare(this.sequenceNo, o.sequenceNo).result();
    }

    /** --- Helper classes --- */

    public static class ByEventSequenceAsc implements Comparator<BillAction>
    {
        @Override
        public int compare(BillAction o1, BillAction o2) {
            return Integer.compare(o1.getSequenceNo(), o2.getSequenceNo());
        }
    }

    public static class ByEventSequenceDesc implements Comparator<BillAction> {
        @Override
        public int compare(BillAction o1, BillAction o2) {
            return Integer.compare(o2.getSequenceNo(), o1.getSequenceNo());
        }
    }

    /** --- Basic Getters/Setters --- */

    public BillId getBillId() {
        return billId;
    }

    public void setBillId(BillId billId) {
        this.billId = billId;
    }

    public int getSequenceNo() {
        return sequenceNo;
    }

    public void setSequenceNo(int sequenceNo) {
        this.sequenceNo = sequenceNo;
    }

    public Chamber getChamber() {
        return chamber;
    }

    public void setChamber(Chamber chamber) {
        this.chamber = chamber;
    }

    public LocalDate getDate() {
        return date;
    }

    public void setDate(LocalDate date) {
        this.date = date;
    }

    public String getText() {
        return text;
    }

    /**
     * Sets the descriptive text for this bill action.
     *
     * @param text the action description
     */
    public void setText(String text) {
        this.text = text;
    }

    /**
     * Gets the type of this bill action.
     *
     * @return the action type, or {@code null} if not set
     */
    public String getType() {
        return type;
    }

    /**
     * Sets the action's type.
     *
     * @param type the descriptive type or category of the action
     */
    public void setType(String type) {
        this.type = type;
    }
}