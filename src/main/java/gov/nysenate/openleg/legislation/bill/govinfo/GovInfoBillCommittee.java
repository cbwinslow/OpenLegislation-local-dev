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

    // Constructors
    public GovInfoBillCommittee() {}

    // Getters/Setters
    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getChamber() { return chamber; }
    public void setChamber(String chamber) { this.chamber = chamber; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillCommittee that = (GovInfoBillCommittee) o;
        return Objects.equals(code, that.code) && Objects.equals(name, that.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(code, name);
    }
}
