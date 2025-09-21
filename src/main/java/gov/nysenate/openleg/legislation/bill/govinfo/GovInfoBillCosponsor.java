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

    // Constructors
    public GovInfoBillCosponsor() {}

    public GovInfoBillCosponsor(String givenName, String familyName, String party, String state,
                                String district, LocalDate dateAdded) {
        this.givenName = givenName;
        this.familyName = familyName;
        this.party = party;
        this.state = state;
        this.district = district;
        this.dateAdded = dateAdded;
    }

    // Getters/Setters
    public String getGivenName() { return givenName; }
    public void setGivenName(String givenName) { this.givenName = givenName; }

    public String getFamilyName() { return familyName; }
    public void setFamilyName(String familyName) { this.familyName = familyName; }

    public String getTermsOfAddress() { return termsOfAddress; }
    public void setTermsOfAddress(String termsOfAddress) { this.termsOfAddress = termsOfAddress; }

    public String getParty() { return party; }
    public void setParty(String party) { this.party = party; }

    public String getState() { return state; }
    public void setState(String state) { this.state = state; }

    public String getDistrict() { return district; }
    public void setDistrict(String district) { this.district = district; }

    public LocalDate getDateAdded() { return dateAdded; }
    public void setDateAdded(LocalDate dateAdded) { this.dateAdded = dateAdded; }

    public Integer getPersonId() { return personId; }
    public void setPersonId(Integer personId) { this.personId = personId; }

    // Dedup helper: normalized key for matching
    public String getMatchKey() {
        String name = (givenName != null ? givenName : "") + " " + (familyName != null ? familyName : "");
        name = name.trim().toLowerCase();
        return name + "|" + (state != null ? state : "") + "|" + (party != null ? party : "");
    }

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

    @Override
    public int hashCode() {
        return Objects.hash(givenName, familyName, party, state, district, dateAdded);
    }

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
