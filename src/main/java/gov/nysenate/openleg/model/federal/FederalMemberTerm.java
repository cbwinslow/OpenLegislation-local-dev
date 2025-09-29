package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;
import java.util.Objects;

/**
 * Represents a term served by a federal legislator.
 */
@Entity
@Table(name = "federal_member_terms", schema = "master")
public class FederalMemberTerm {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id", nullable = false)
    private FederalMember member;

    @Column(name = "congress", nullable = false)
    private Integer congress;

    @Column(name = "start_year", nullable = false)
    private Integer startYear;

    @Column(name = "end_year")
    private Integer endYear;

    @Column(name = "party", length = 1)
    private String party;

    @Column(name = "state", length = 2)
    private String state;

    @Column(name = "district")
    private String district;

    @Column(name = "chamber", nullable = false)
    @Enumerated(EnumType.STRING)
    private FederalChamber chamber;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDate updatedAt;

    // Constructors
    public FederalMemberTerm() {
        this.createdAt = LocalDate.now();
    }

    public FederalMemberTerm(FederalMember member, Integer congress, Integer startYear, FederalChamber chamber) {
        this();
        this.member = member;
        this.congress = congress;
        this.startYear = startYear;
        this.chamber = chamber;
    }

    // Getters and Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public FederalMember getMember() {
        return member;
    }

    public void setMember(FederalMember member) {
        this.member = member;
    }

    public Integer getCongress() {
        return congress;
    }

    public void setCongress(Integer congress) {
        this.congress = congress;
    }

    public Integer getStartYear() {
        return startYear;
    }

    public void setStartYear(Integer startYear) {
        this.startYear = startYear;
    }

    public Integer getEndYear() {
        return endYear;
    }

    public void setEndYear(Integer endYear) {
        this.endYear = endYear;
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

    public String getDistrict() {
        return district;
    }

    public void setDistrict(String district) {
        this.district = district;
    }

    public FederalChamber getChamber() {
        return chamber;
    }

    public void setChamber(FederalChamber chamber) {
        this.chamber = chamber;
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
    public boolean isActive() {
        int currentYear = LocalDate.now().getYear();
        return startYear <= currentYear && (endYear == null || endYear >= currentYear);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        FederalMemberTerm that = (FederalMemberTerm) o;
        return Objects.equals(member, that.member) &&
               Objects.equals(congress, that.congress) &&
               Objects.equals(chamber, that.chamber);
    }

    @Override
    public int hashCode() {
        return Objects.hash(member, congress, chamber);
    }

    @Override
    public String toString() {
        return "FederalMemberTerm{" +
                "id=" + id +
                ", member=" + (member != null ? member.getBioguideId() : "null") +
                ", congress=" + congress +
                ", startYear=" + startYear +
                ", endYear=" + endYear +
                ", chamber=" + chamber +
                '}';
    }
}