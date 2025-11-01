package gov.nysenate.openleg.legislation.bill.govinfo;

import java.time.LocalDate;
import java.util.Objects;

/**
 * Represents a cosponsor in a GovInfo bill document.
 * Parsed from XML <cosponsor> elements.
 * Maps to SQL bill_cosponsor table, linking to federal_member via lookup.
 */
public class GovInfoBillCosponsor {
    private String givenName;
    private String familyName;
    private String termsOfAddress; // e.g., "Hon."
    private String party;
    private String state;
    private String district;
    private LocalDate dateAdded;
    private Integer personId; // FK to federal_person.id, set after DB lookup/dedup

    /**
 * Creates an empty GovInfoBillCosponsor instance.
 *
 * <p>All fields are left unset and should be populated via setters or by parsing a source
 * (e.g., a GovInfo XML <cosponsor> element).</p>
 */
    public GovInfoBillCosponsor() {}

    /**
     * Construct a GovInfoBillCosponsor with the provided name, party, state, district, and dateAdded.
     *
     * @param givenName  the cosponsor's given (first) name
     * @param familyName the cosponsor's family (last) name
     * @param party      the cosponsor's party affiliation (may be null)
     * @param state      the cosponsor's state (e.g., two‑letter code, may be null)
     * @param district   the cosponsor's district (may be null)
     * @param dateAdded  the date the cosponsor was added to the bill (may be null)
     */
    public GovInfoBillCosponsor(String givenName, String familyName, String party, String state,
                                String district, LocalDate dateAdded) {
        this.givenName = givenName;
        this.familyName = familyName;
        this.party = party;
        this.state = state;
        this.district = district;
        this.dateAdded = dateAdded;
    }

    /**
 * Gets the cosponsor's given (first) name.
 *
 * @return the given name, or null if not set
 */
    public String getGivenName() { return givenName; }
    /**
 * Sets the given (first) name of the cosponsor.
 *
 * @param givenName the given name to set, or {@code null} if not available
 */
public void setGivenName(String givenName) { this.givenName = givenName; }

    /**
 * Gets the cosponsor's family name.
 *
 * @return the family name, or {@code null} if not set
 */
public String getFamilyName() { return familyName; }
    /**
 * Sets the cosponsor's family (last) name.
 *
 * @param familyName the family/last name of the cosponsor, or {@code null} if not provided
 */
public void setFamilyName(String familyName) { this.familyName = familyName; }

    /**
 * Gets the cosponsor's honorific or terms of address.
 *
 * @return the terms of address (e.g., "Hon."), or null if not present.
 */
public String getTermsOfAddress() { return termsOfAddress; }
    /**
 * Sets the cosponsor's terms of address.
 *
 * @param termsOfAddress the honorific or title used before the name (for example "Hon.")
 */
public void setTermsOfAddress(String termsOfAddress) { this.termsOfAddress = termsOfAddress; }

    /**
 * Gets the cosponsor's party affiliation.
 *
 * @return the party affiliation, or null if not specified
 */
public String getParty() { return party; }
    /**
 * Set the cosponsor's party affiliation.
 *
 * @param party the party affiliation (may be null)
 */
public void setParty(String party) { this.party = party; }

    /**
 * Gets the cosponsor's state or jurisdiction.
 *
 * @return the state value for the cosponsor, or {@code null} if not set
 */
public String getState() { return state; }
    /**
 * Sets the cosponsor's state.
 *
 * @param state the cosponsor's state (e.g., "NY")
 */
public void setState(String state) { this.state = state; }

    /**
 * Gets the cosponsor's congressional district.
 *
 * @return the district identifier (e.g., "12"), or {@code null} if not set
 */
public String getDistrict() { return district; }
    /**
 * Sets the cosponsor's district.
 *
 * @param district the cosponsor's district (e.g., "12", "At-Large"), or null to clear it
 */
public void setDistrict(String district) { this.district = district; }

    /**
 * Gets the date the cosponsor was added to the bill as reported in the GovInfo document.
 *
 * @return the date the cosponsor was added, or {@code null} if the date is not present
 */
public LocalDate getDateAdded() { return dateAdded; }
    /**
 * Set the date the cosponsor was added.
 *
 * @param dateAdded the date the cosponsor was added, or {@code null} if unknown
 */
public void setDateAdded(LocalDate dateAdded) { this.dateAdded = dateAdded; }

    /**
 * Gets the foreign-key identifier linking this cosponsor to a federal person record.
 *
 * @return the `personId` referencing `federal_person.id`, or `null` if no match has been resolved
 */
public Integer getPersonId() { return personId; }
    /**
 * Sets the foreign key referencing the associated federal person record.
 *
 * @param personId the `federal_person.id` to link to this cosponsor, or `null` to clear the association
 */
public void setPersonId(Integer personId) { this.personId = personId; }

    /**
     * Constructs a normalized deduplication key for matching cosponsor records.
     *
     * The key is the lowercased concatenation of the cosponsor's full name,
     * state, and party separated by pipe characters.
     *
     * @return the normalized key in the form "givenName familyName|state|party";
     *         null name/state/party values are treated as empty strings and the
     *         full name is trimmed and lowercased.
     */
    public String getMatchKey() {
        String name = (givenName != null ? givenName : "") + " " + (familyName != null ? familyName : "");
        name = name.trim().toLowerCase();
        return name + "|" + (state != null ? state : "") + "|" + (party != null ? party : "");
    }

    /**
     * Determine whether another object represents the same cosponsor.
     *
     * Compares givenName, familyName, party, state, district, and dateAdded for equality.
     *
     * @param o the object to compare with
     * @return `true` if the specified object is a GovInfoBillCosponsor with equal givenName, familyName, party, state, district, and dateAdded; `false` otherwise
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBillCosponsor that = (GovInfoBillCosponsor) o;
        return Objects.equals(givenName, that.givenName) &&
               Objects.equals(familyName, that.familyName) &&
               Objects.equals(party, that.party) &&
               Objects.equals(state, that.state) &&
               Objects.equals(district, that.district) &&
               Objects.equals(dateAdded, that.dateAdded);
    }

    /**
     * Computes a hash code for this cosponsor.
     *
     * @return the hash code derived from givenName, familyName, party, state, district, and dateAdded
     */
    @Override
    public int hashCode() {
        return Objects.hash(givenName, familyName, party, state, district, dateAdded);
    }

    /**
     * String representation of the cosponsor including given and family names, party, state, district, date added, and personId.
     *
     * @return a string containing the cosponsor's givenName, familyName, party, state, district, dateAdded, and personId
     */
    @Override
    public String toString() {
        return "GovInfoBillCosponsor{" +
                "givenName='" + givenName + '\'' +
                ", familyName='" + familyName + '\'' +
                ", party='" + party + '\'' +
                ", state='" + state + '\'' +
                ", district='" + district + '\'' +
                ", dateAdded=" + dateAdded +
                ", personId=" + personId +
                '}';
    }
}