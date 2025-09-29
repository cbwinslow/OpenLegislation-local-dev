package gov.nysenate.openleg.model.federal;

import javax.persistence.*;
import java.time.LocalDate;
import java.util.Objects;

/**
 * Represents a committee assignment for a federal legislator.
 */
@Entity
@Table(name = "federal_member_committees", schema = "master")
public class FederalMemberCommittee {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id", nullable = false)
    private FederalMember member;

    @Column(name = "committee_name", nullable = false)
    private String committeeName;

    @Column(name = "committee_code")
    private String committeeCode;

    @Column(name = "chamber")
    @Enumerated(EnumType.STRING)
    private FederalChamber chamber;

    @Column(name = "role", length = 50)
    private String role; // e.g., "Chair", "Ranking Member", "Member"

    @Column(name = "start_date")
    private LocalDate startDate;

    @Column(name = "end_date")
    private LocalDate endDate;

    @Column(name = "subcommittee")
    private String subcommittee;

    @Column(name = "created_at", nullable = false)
    private LocalDate createdAt;

    // Constructors
    public FederalMemberCommittee() {
        this.createdAt = LocalDate.now();
    }

    public FederalMemberCommittee(FederalMember member, String committeeName, FederalChamber chamber) {
        this();
        this.member = member;
        this.committeeName = committeeName;
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

    public String getCommitteeName() {
        return committeeName;
    }

    public void setCommitteeName(String committeeName) {
        this.committeeName = committeeName;
    }

    public String getCommitteeCode() {
        return committeeCode;
    }

    public void setCommitteeCode(String committeeCode) {
        this.committeeCode = committeeCode;
    }

    public FederalChamber getChamber() {
        return chamber;
    }

    public void setChamber(FederalChamber chamber) {
        this.chamber = chamber;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public LocalDate getStartDate() {
        return startDate;
    }

    public void setStartDate(LocalDate startDate) {
        this.startDate = startDate;
    }

    public LocalDate getEndDate() {
        return endDate;
    }

    public void setEndDate(LocalDate endDate) {
        this.endDate = endDate;
    }

    public String getSubcommittee() {
        return subcommittee;
    }

    public void setSubcommittee(String subcommittee) {
        this.subcommittee = subcommittee;
    }

    public LocalDate getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDate createdAt) {
        this.createdAt = createdAt;
    }

    // Business methods
    public boolean isActive() {
        LocalDate now = LocalDate.now();
        return startDate != null && startDate.isBefore(now) &&
               (endDate == null || endDate.isAfter(now));
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        FederalMemberCommittee that = (FederalMemberCommittee) o;
        return Objects.equals(member, that.member) &&
               Objects.equals(committeeName, that.committeeName) &&
               Objects.equals(chamber, that.chamber) &&
               Objects.equals(subcommittee, that.subcommittee);
    }

    @Override
    public int hashCode() {
        return Objects.hash(member, committeeName, chamber, subcommittee);
    }

    @Override
    public String toString() {
        return "FederalMemberCommittee{" +
                "id=" + id +
                ", member=" + (member != null ? member.getBioguideId() : "null") +
                ", committeeName='" + committeeName + '\'' +
                ", chamber=" + chamber +
                ", role='" + role + '\'' +
                ", active=" + isActive() +
                '}';
    }
}