package gov.nysenate.openleg.legislation.bill.govinfo;

import java.time.LocalDate;
import java.util.Objects;

/**
 * Represents the primary sponsor of a GovInfo bill document.
 * Similar to Cosponsor but marked as primary sponsor.
 * Parsed from XML <sponsor> elements.
 */
public class GovInfoBillSponsor extends GovInfoBillCosponsor {
    private boolean isPrimary = true;

    /**
     * Creates a GovInfoBillSponsor with default (empty) sponsor fields and `isPrimary` set to `true`.
     */
    public GovInfoBillSponsor() {
        super();
    }

    /**
     * Creates a primary sponsor with the specified personal and affiliation details.
     *
     * @param givenName the sponsor's given (first) name
     * @param familyName the sponsor's family (last) name
     * @param party the sponsor's political party
     * @param state the sponsor's state abbreviation
     * @param district the sponsor's district identifier
     * @param dateAdded the date the sponsor was added to the bill record
     */
    public GovInfoBillSponsor(String givenName, String familyName, String party, String state,
                              String district, LocalDate dateAdded) {
        super(givenName, familyName, party, state, district, dateAdded);
    }

    /**
 * Indicates whether this sponsor is the primary sponsor.
 *
 * @return `true` if this sponsor is primary, `false` otherwise.
 */
    public boolean isPrimary() { return isPrimary; }
    /**
 * Sets whether this sponsor is the primary sponsor of the bill.
 *
 * @param primary true if the sponsor should be marked as primary, false otherwise
 */
public void setPrimary(boolean primary) { isPrimary = primary; }

    /**
     * Produces a match key identifying this sponsor instance including a primary indicator.
     *
     * @return the superclass match key with "|primary" appended
     */
    @Override
    public String getMatchKey() {
        return super.getMatchKey() + "|primary";
    }

    /**
     * Compare this GovInfoBillSponsor to another object for value equality.
     *
     * Equality is true when the other object is a GovInfoBillSponsor, the superclass
     * fields are equal, and the `isPrimary` flag matches.
     *
     * @param o the object to compare with
     * @return `true` if the objects are equal, `false` otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!super.equals(o)) return false;
        GovInfoBillSponsor that = (GovInfoBillSponsor) o;
        return isPrimary() == that.isPrimary();
    }

    /**
     * Computes a hash code for this sponsor that includes the primary flag.
     *
     * @return the hash code value for this object, incorporating the superclass hash and the primary flag
     */
    @Override
    public int hashCode() {
        return Objects.hash(super.hashCode(), isPrimary());
    }

    /**
     * String representation of the sponsor including superclass data and the primary flag.
     *
     * @return a string containing the superclass' toString content followed by ", isPrimary=" and the primary flag value
     */
    @Override
    public String toString() {
        return "GovInfoBillSponsor{" + super.toString() + ", isPrimary=" + isPrimary + '}';
    }
}