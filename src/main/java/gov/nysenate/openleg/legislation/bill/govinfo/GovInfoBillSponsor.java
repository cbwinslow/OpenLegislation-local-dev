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
     * Constructs a new GovInfoBillSponsor with default (empty) fields; the sponsor is marked as primary by default.
     */
    public GovInfoBillSponsor() {
        super();
    }

    /**
     * Creates a GovInfoBillSponsor with the given personal and jurisdictional details; the sponsor's primary flag defaults to true.
     *
     * @param givenName the sponsor's given (first) name
     * @param familyName the sponsor's family (last) name
     * @param party the sponsor's party affiliation (may be null or empty if unknown)
     * @param state the sponsor's state abbreviation
     * @param district the sponsor's district identifier (may be null or empty if not applicable)
     * @param dateAdded the date the sponsor was added to the bill document (may be null if unknown)
     */
    public GovInfoBillSponsor(String givenName, String familyName, String party, String state,
                              String district, LocalDate dateAdded) {
        super(givenName, familyName, party, state, district, dateAdded);
    }

    /**
 * Indicates whether this sponsor is marked as the primary sponsor.
 *
 * @return `true` if the sponsor is primary, `false` otherwise.
 */
    public boolean isPrimary() { return isPrimary; }
    /**
 * Set whether this sponsor is the primary sponsor.
 *
 * @param primary `true` if this sponsor is primary, `false` otherwise
 */
public void setPrimary(boolean primary) { isPrimary = primary; }

    /**
     * Constructs the match key for this sponsor and appends a primary marker.
     *
     * @return the match key with the suffix "|primary"
     */
    @Override
    public String getMatchKey() {
        return super.getMatchKey() + "|primary";
    }

    /**
     * Determines whether another object is equal to this GovInfoBillSponsor, including the primary-sponsor flag.
     *
     * @param o the object to compare with this instance
     * @return `true` if `o` is a GovInfoBillSponsor whose superclass state is equal and whose `isPrimary` value matches, `false` otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!super.equals(o)) return false;
        GovInfoBillSponsor that = (GovInfoBillSponsor) o;
        return isPrimary() == that.isPrimary();
    }

    /**
     * Computes a hash code that incorporates the superclass state and the sponsor's primary flag.
     *
     * @return an int hash code reflecting the superclass state and the `isPrimary` value
     */
    @Override
    public int hashCode() {
        return Objects.hash(super.hashCode(), isPrimary());
    }

    /**
     * Provides a string representation that includes the superclass representation and the primary flag.
     *
     * @return the string representation of this GovInfoBillSponsor, containing the superclass's representation and the `isPrimary` value
     */
    @Override
    public String toString() {
        return "GovInfoBillSponsor{" + super.toString() + ", isPrimary=" + isPrimary + '}';
    }
}