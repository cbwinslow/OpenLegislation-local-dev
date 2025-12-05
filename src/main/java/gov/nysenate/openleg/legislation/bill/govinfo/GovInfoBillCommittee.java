package gov.nysenate.openleg.legislation.bill.govinfo;

import java.util.Objects;

/**
 * Represents a committee associated with a GovInfo bill.
 * Parsed from XML <committee> or action references; may link to member committee assignments.
 */
public class GovInfoBillCommittee {
    private String code;
    private String name;
    private String chamber; // 'house' or 'senate'

    /**
 * Creates an empty GovInfoBillCommittee instance.
 *
 * The new instance has no code, name, or chamber set. Fields may be populated via setters.
 */
    public GovInfoBillCommittee() {}

    /**
 * Provides the committee code.
 *
 * @return the committee code, or {@code null} if not set
 */
    public String getCode() { return code; }
    /**
 * Sets the committee code.
 *
 * @param code the committee code identifier
 */
public void setCode(String code) { this.code = code; }

    /**
 * Retrieves the committee name.
 *
 * @return the committee name, or null if not set
 */
public String getName() { return name; }
    /**
 * Sets the committee's name.
 *
 * @param name the committee's name
 */
public void setName(String name) { this.name = name; }

    /**
 * Get the committee's legislative chamber designation.
 *
 * @return the chamber designation, e.g. {@code "house"} or {@code "senate"}, or {@code null} if not set
 */
public String getChamber() { return chamber; }
    /**
 * Sets the chamber designation for this committee.
 *
 * @param chamber the chamber identifier, typically "house" or "senate"
 */
public void setChamber(String chamber) { this.chamber = chamber; }

    /**
     * Check equality with another object based on the committee's code and name.
     *
     * @param o the object to compare with
     * @return `true` if the given object is a GovInfoBillCommittee with the same code and name, `false` otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillCommittee that = (GovInfoBillCommittee) o;
        return Objects.equals(code, that.code) && Objects.equals(name, that.name);
    }

    /**
     * Compute a hash code based on the committee's code and name.
     *
     * @return the hash code derived from this committee's `code` and `name`
     */
    @Override
    public int hashCode() {
        return Objects.hash(code, name);
    }
}