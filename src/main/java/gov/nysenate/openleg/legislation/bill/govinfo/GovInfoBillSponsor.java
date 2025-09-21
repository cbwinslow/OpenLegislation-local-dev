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

    // Constructors
    public GovInfoBillSponsor() {
        super();
    }

    public GovInfoBillSponsor(String givenName, String familyName, String party, String state,
                              String district, LocalDate dateAdded) {
        super(givenName, familyName, party, state, district, dateAdded);
    }

    // Getters/Setters
    public boolean isPrimary() { return isPrimary; }
    public void setPrimary(boolean primary) { isPrimary = primary; }

    @Override
    public String getMatchKey() {
        return super.getMatchKey() + "|primary";
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!super.equals(o)) return false;
        GovInfoBillSponsor that = (GovInfoBillSponsor) o;
        return isPrimary() == that.isPrimary();
    }

    @Override
    public int hashCode() {
        return Objects.hash(super.hashCode(), isPrimary());
    }

    @Override
    public String toString() {
        return "GovInfoBillSponsor{" + super.toString() + ", isPrimary=" + isPrimary + '}';
    }
}
