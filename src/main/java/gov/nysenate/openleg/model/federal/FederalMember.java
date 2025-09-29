package gov.nysenate.openleg.model.federal;

import java.util.List;

public class FederalMember {
    private String bioguideId;
    private String fullName;
    private String firstName;
    private String lastName;
    private String party;
    private String state;
    private String chamber;
    private boolean currentMember;
    private List<Object> terms;  // JSONB in DB
    private List<Object> committees;  // JSONB
    private Object socialMedia;  // JSONB

    // Constructors
    public FederalMember() {}

    public FederalMember(String bioguideId, String fullName) {
        this.bioguideId = bioguideId;
        this.fullName = fullName;
    }

    // Getters and Setters
    public String getBioguideId() {
        return bioguideId;
    }

    public void setBioguideId(String bioguideId) {
        this.bioguideId = bioguideId;
    }

    public String getFullName() {
        return fullName;
    }

    public void setFullName(String fullName) {
        this.fullName = fullName;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public String getParty() {
        return party;
    }

    public void setParty(String party) {
        this.party = party;
    }

    public String getState() {
        return state;
    }

    public void setState(String state) {
        this.state = state;
    }

    public String getChamber() {
        return chamber;
    }

    public void setChamber(String chamber) {
        this.chamber = chamber;
    }

    public boolean isCurrentMember() {
        return currentMember;
    }

    public void setCurrentMember(boolean currentMember) {
        this.currentMember = currentMember;
    }

    public List<Object> getTerms() {
        return terms;
    }

    public void setTerms(List<Object> terms) {
        this.terms = terms;
    }

    public List<Object> getCommittees() {
        return committees;
    }

    public void setCommittees(List<Object> committees) {
        this.committees = committees;
    }

    public Object getSocialMedia() {
        return socialMedia;
    }

    public void setSocialMedia(Object socialMedia) {
        this.socialMedia = socialMedia;
    }
}
