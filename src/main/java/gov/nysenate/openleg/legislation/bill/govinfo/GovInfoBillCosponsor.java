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
 * Creates an empty GovInfoBillCosponsor with all properties unset.
 */
    public GovInfoBillCosponsor() {}

    /**
     * Constructs a GovInfoBillCosponsor with the specified name, party, state, district, and date added.
     *
     * @param givenName the cosponsor's given (first) name
     * @param familyName the cosponsor's family (last) name
     * @param party the cosponsor's political party
     * @param state the cosponsor's state abbreviation
     * @param district the cosponsor's electoral district
     * @param dateAdded the date the cosponsor was added
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
 * @return the cosponsor's given name, or {@code null} if not set
 */
    public String getGivenName() { return givenName; }
    /**
 * Sets the cosponsor's given name.
 *
 * @param givenName the cosponsor's given (first) name
 */
public void setGivenName(String givenName) { this.givenName = givenName; }

    /**
 * The cosponsor's family name (surname).
 *
 * @return the cosponsor's family name (surname), or null if not set.
 */
public String getFamilyName() { return familyName; }
    /**
 * Sets the cosponsor's family (last) name.
 *
 * @param familyName the family name of the cosponsor
 */
public void setFamilyName(String familyName) { this.familyName = familyName; }

    /**
 * Gets the cosponsor's formal terms of address (for example, "Hon.").
 *
 * @return the terms of address, or {@code null} if not provided
 */
public String getTermsOfAddress() { return termsOfAddress; }
    /**
 * Sets the honorific or form of address for the cosponsor.
 *
 * @param termsOfAddress the honorific (e.g., "Hon.") or title to use for the cosponsor; may be null
 */
public void setTermsOfAddress(String termsOfAddress) { this.termsOfAddress = termsOfAddress; }

    /**
 * Gets the cosponsor's political party affiliation.
 *
 * @return the party abbreviation or name for the cosponsor, or {@code null} if not set
 */
public String getParty() { return party; }
    /**
 * Set the cosponsor's political party.
 *
 * @param party the party name or abbreviation (may be {@code null})
 */
public void setParty(String party) { this.party = party; }

    /**
 * Gets the cosponsor's state abbreviation.
 *
 * @return the two-letter state abbreviation (e.g., "NY"), or {@code null} if not set
 */
public String getState() { return state; }
    /**
 * Sets the cosponsor's state abbreviation.
 *
 * @param state two-letter state abbreviation (e.g., {@code NY})
 */
public void setState(String state) { this.state = state; }

    /**
 * Gets the cosponsor's electoral district.
 *
 * @return the electoral district identifier (e.g., district number or code), or {@code null} if not set
 */
public String getDistrict() { return district; }
    /**
 * Set the cosponsor's electoral district.
 *
 * @param district the electoral district (e.g., "12"), or {@code null} if unknown
 */
public void setDistrict(String district) { this.district = district; }

    /**
 * Date the cosponsor was added.
 *
 * @return the date the cosponsor was added, or {@code null} if not set
 */
public LocalDate getDateAdded() { return dateAdded; }
    /**
 * Sets the date the cosponsor was added.
 *
 * @param dateAdded the date the cosponsor was added
 */
public void setDateAdded(LocalDate dateAdded) { this.dateAdded = dateAdded; }

    /**
 * The identifier of the matched federal person for this cosponsor.
 *
 * @return the foreign key to `federal_person.id`, or `null` if no person has been resolved
 */
public Integer getPersonId() { return personId; }
    /**
 * Sets the foreign key linking this cosponsor to a resolved federal person record.
 *
 * @param personId the `federal_person.id` value to associate with this cosponsor, or `null` if not yet resolved
 */
public void setPersonId(Integer personId) { this.personId = personId; }

    /**
     * Builds a normalized deduplication key for matching cosponsors.
     *
     * @return a normalized string key in the form "givenName familyName|state|party" where the name is trimmed and lowercased,
     *         and null fields are treated as empty strings
     */
    public String getMatchKey() {
        String name = (givenName != null ? givenName : "") + " " + (familyName != null ? familyName : "");
        name = name.trim().toLowerCase();
        return name + "|" + (state != null ? state : "") + "|" + (party != null ? party : "");
    }

    /**
     * Determines whether another object represents the same cosponsor based on givenName, familyName, party, state, district, and dateAdded.
     *
     * @param o the object to compare with
     * @return true if the other object is a GovInfoBillCosponsor with equal givenName, familyName, party, state, district, and dateAdded, false otherwise
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
     * Computes a hash code derived from the cosponsor's core identity fields.
     *
     * @return the hash code computed from givenName, familyName, party, state, district, and dateAdded
     */
    @Override
    public int hashCode() {
        return Objects.hash(givenName, familyName, party, state, district, dateAdded);
    }

    /**
     * String representation of the cosponsor including core identity fields and the resolved personId.
     *
     * @return a string containing givenName, familyName, party, state, district, dateAdded, and personId
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