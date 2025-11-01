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
 * Creates a new GovInfoBillCommittee used to represent a committee associated with GovInfo bill data.
 *
 * <p>Fields `code`, `name`, and `chamber` are initialized to null.</p>
 */
    public GovInfoBillCommittee() {}

    /**
 * Retrieve the committee code as provided by GovInfo.
 *
 * @return the committee code, or {@code null} if not set
 */
    public String getCode() { return code; }
    /**
 * Sets the committee code identifier parsed from GovInfo data.
 *
 * @param code the committee's code (may be null if not present)
 */
public void setCode(String code) { this.code = code; }

    /**
 * Gets the committee's display name.
 *
 * @return the committee name, or null if not set
 */
public String getName() { return name; }
    /**
 * Sets the committee's name.
 *
 * @param name the committee name
 */
public void setName(String name) { this.name = name; }

    /**
 * Gets the committee's legislative chamber.
 *
 * @return the committee chamber identifier, typically "house" or "senate", or {@code null} if unspecified.
 */
public String getChamber() { return chamber; }
    /**
 * Set the chamber for this committee; expected values are "house" or "senate".
 *
 * @param chamber the chamber name ("house" or "senate")
 */
public void setChamber(String chamber) { this.chamber = chamber; }

    /**
     * Determine whether the given object represents the same committee by comparing `code` and `name`.
     *
     * @param o the object to compare with this committee
     * @return `true` if `o` is a {@code GovInfoBillCommittee} with equal `code` and `name`, `false` otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillCommittee that = (GovInfoBillCommittee) o;
        return Objects.equals(code, that.code) && Objects.equals(name, that.name);
    }

    /**
     * Computes a hash code for this committee using its `code` and `name` fields.
     *
     * @return the hash code derived from the committee's `code` and `name`
     */
    @Override
    public int hashCode() {
        return Objects.hash(code, name);
    }
}