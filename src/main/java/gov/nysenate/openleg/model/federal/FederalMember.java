package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Represents a federal legislator (Senator or Representative) with comprehensive biographical
 * and political information from congress.gov and govinfo.gov sources.
 */
@Entity
@Table(name = "federal_members", schema = "master")
public class FederalMember {

    @Id
    @Column(name = "id")
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "bioguide_id", unique = true, nullable = false)
    private String bioguideId;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    @Column(name = "first_name")
    private String firstName;

    @Column(name = "last_name")
    private String lastName;

    @Column(name = "chamber", nullable = false)
    @Enumerated(EnumType.STRING)
    private FederalChamber chamber;

    @Column(name = "state", length = 2)
    private String state;

    @Column(name = "district")
    private String district;

    @Column(name = "party", length = 1)
    private String party;

    @Column(name = "current_member", nullable = false)
    private boolean currentMember = true;

    @OneToMany(mappedBy = "member", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<FederalMemberTerm> terms = new ArrayList<>();

    @OneToMany(mappedBy = "member", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<FederalMemberCommittee> committees = new ArrayList<>();

    @OneToMany(mappedBy = "member", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<FederalMemberSocialMedia> socialMedia = new ArrayList<>();

    @Column(name = "office_address", columnDefinition = "TEXT")
    private String officeAddress;

    @Column(name = "office_phone")
    private String officePhone;

    @Column(name = "office_fax")
    private String officeFax;

    @Column(name = "website_url")
    private String websiteUrl;

    @Column(name = "leadership_positions", columnDefinition = "TEXT[]")
    private String[] leadershipPositions;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDate updatedAt;

    // Constructors
    public FederalMember() {
        this.createdAt = LocalDate.now();
        this.updatedAt = LocalDate.now();
    }

    public FederalMember(String bioguideId, String fullName, FederalChamber chamber) {
        this();
        this.bioguideId = bioguideId;
        this.fullName = fullName;
        this.chamber = chamber;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

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

    public FederalChamber getChamber() {
        return chamber;
    }

    public void setChamber(FederalChamber chamber) {
        this.chamber = chamber;
    }

    public String getState() {
        return state;
    }

    public void setState(String state) {
        this.state = state;
    }

    public String getDistrict() {
        return district;
    }

    public void setDistrict(String district) {
        this.district = district;
    }

    public String getParty() {
        return party;
    }

    public void setParty(String party) {
        this.party = party;
    }

    public boolean isCurrentMember() {
        return currentMember;
    }

    public void setCurrentMember(boolean currentMember) {
        this.currentMember = currentMember;
    }

    public List<FederalMemberTerm> getTerms() {
        return terms;
    }

    public void setTerms(List<FederalMemberTerm> terms) {
        this.terms = terms;
    }

    public List<FederalMemberCommittee> getCommittees() {
        return committees;
    }

    public void setCommittees(List<FederalMemberCommittee> committees) {
        this.committees = committees;
    }

    public List<FederalMemberSocialMedia> getSocialMedia() {
        return socialMedia;
    }

    public void setSocialMedia(List<FederalMemberSocialMedia> socialMedia) {
        this.socialMedia = socialMedia;
    }

    public String getOfficeAddress() {
        return officeAddress;
    }

    public void setOfficeAddress(String officeAddress) {
        this.officeAddress = officeAddress;
    }

    public String getOfficePhone() {
        return officePhone;
    }

    public void setOfficePhone(String officePhone) {
        this.officePhone = officePhone;
    }

    public String getOfficeFax() {
        return officeFax;
    }

    public void setOfficeFax(String officeFax) {
        this.officeFax = officeFax;
    }

    public String getWebsiteUrl() {
        return websiteUrl;
    }

    public void setWebsiteUrl(String websiteUrl) {
        this.websiteUrl = websiteUrl;
    }

    public String[] getLeadershipPositions() {
        return leadershipPositions;
    }

    public void setLeadershipPositions(String[] leadershipPositions) {
        this.leadershipPositions = leadershipPositions;
    }

    public LocalDate getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDate createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDate getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDate updatedAt) {
        this.updatedAt = updatedAt;
    }

    // Business methods
    public FederalMemberTerm getCurrentTerm() {
        return terms.stream()
                .filter(term -> term.getEndYear() == null || term.getEndYear() >= LocalDate.now().getYear())
                .findFirst()
                .orElse(null);
    }

    public List<FederalMemberCommittee> getCurrentCommittees() {
        return committees.stream()
                .filter(committee -> committee.getEndDate() == null || committee.getEndDate().isAfter(LocalDate.now()))
                .toList();
    }

    public FederalMemberSocialMedia getSocialMediaAccount(String platform) {
        return socialMedia.stream()
                .filter(sm -> platform.equalsIgnoreCase(sm.getPlatform()))
                .findFirst()
                .orElse(null);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        FederalMember that = (FederalMember) o;
        return Objects.equals(bioguideId, that.bioguideId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(bioguideId);
    }

    @Override
    public String toString() {
        return "FederalMember{" +
                "id=" + id +
                ", bioguideId='" + bioguideId + '\'' +
                ", fullName='" + fullName + '\'' +
                ", chamber=" + chamber +
                ", state='" + state + '\'' +
                ", district='" + district + '\'' +
                ", party='" + party + '\'' +
                ", currentMember=" + currentMember +
                '}';
    }
}