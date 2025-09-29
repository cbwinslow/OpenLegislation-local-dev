package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "federal_members", schema = "master")
public class FederalMember {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "person_id", nullable = false)
    private Long personId;

    @Column(name = "bioguide_id", unique = true, nullable = false)
    private String bioguideId;

    @Column(name = "full_name")
    private String fullName;

    @Column(name = "first_name")
    private String firstName;

    @Column(name = "middle_name")
    private String middleName;

    @Column(name = "last_name")
    private String lastName;

    @Column(name = "suffix")
    private String suffix;

    @Column(name = "nickname")
    private String nickname;

    @Column(name = "birth_year")
    private Integer birthYear;

    @Column(name = "death_year")
    private Integer deathYear;

    @Column(name = "gender")
    private String gender;

    @Column(name = "chamber", nullable = false)
    @Enumerated(EnumType.STRING)
    private FederalChamber chamber;

    @Column(name = "state")
    private String state;

    @Column(name = "district")
    private String district;

    @Column(name = "party")
    private String party;

    @Column(name = "current_member", nullable = false)
    private Boolean currentMember = true;

    @Column(name = "office_address")
    private String officeAddress;

    @Column(name = "office_phone")
    private String officePhone;

    @Column(name = "website_url")
    private String websiteUrl;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDate updatedAt;

    @OneToMany(mappedBy = "member", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<FederalMemberTerm> terms = new ArrayList<>();

    @OneToMany(mappedBy = "member", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<FederalMemberSocialMedia> socialMedia = new ArrayList<>();

    // Constructors
    public FederalMember() {
        this.createdAt = LocalDate.now();
        this.updatedAt = LocalDate.now();
    }

    public FederalMember(String bioguideId, String fullName) {
        this();
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

    public String getDistrict() {
        return district;
    }

    public void setDistrict(String district) {
        this.district = district;
    }

    public Boolean getCurrentMember() {
        return currentMember;
    }

    public void setCurrentMember(Boolean currentMember) {
        this.currentMember = currentMember;
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

    public String getWebsiteUrl() {
        return websiteUrl;
    }

    public void setWebsiteUrl(String websiteUrl) {
        this.websiteUrl = websiteUrl;
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

    public List<FederalMemberTerm> getTerms() {
        return terms;
    }

    public void setTerms(List<FederalMemberTerm> terms) {
        this.terms = terms;
    }

    public List<FederalMemberSocialMedia> getSocialMedia() {
        return socialMedia;
    }

    public void setSocialMedia(List<FederalMemberSocialMedia> socialMedia) {
        this.socialMedia = socialMedia;
    }

    @Override
    public String toString() {
        return "FederalMember{" +
                "id=" + id +
                ", bioguideId='" + bioguideId + '\'' +
                ", fullName='" + fullName + '\'' +
                ", chamber=" + chamber +
                ", state='" + state + '\'' +
                ", party='" + party + '\'' +
                ", currentMember=" + currentMember +
                '}';
    }
}
