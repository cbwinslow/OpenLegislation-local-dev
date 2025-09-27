package gov.nysenate.openleg.legislation.bill.govinfo;

import java.time.LocalDate;
import java.util.List;
import java.util.Objects;

/**
 * Represents a federal bill from GovInfo documents.
 * Parsed from XML <bill> elements.
 * Includes sponsors and cosponsors with dedup linkage to federal members.
 */
public class GovInfoBill {
    private String congressNumber;
    private String sessionNumber;
    private String billNumber;
    private String billType; // e.g., "hr", "s"
    private GovInfoBillSponsor sponsor;
    private List<GovInfoBillCosponsor> cosponsors;
    private List<GovInfoBillAction> actions;
    private GovInfoBillText text;
    private List<GovInfoBillCommittee> committees;
    private List<GovInfoDocRef> docRefs;

    // Constructors
    public GovInfoBill() {}

    public GovInfoBill(String congressNumber, String sessionNumber, String billNumber, String billType,
                       GovInfoBillSponsor sponsor) {
        this.congressNumber = congressNumber;
        this.sessionNumber = sessionNumber;
        this.billNumber = billNumber;
        this.billType = billType;
        this.sponsor = sponsor;
    }

    // Getters/Setters
    public String getCongressNumber() { return congressNumber; }
    public void setCongressNumber(String congressNumber) { this.congressNumber = congressNumber; }

    public String getSessionNumber() { return sessionNumber; }
    public void setSessionNumber(String sessionNumber) { this.sessionNumber = sessionNumber; }

    public String getBillNumber() { return billNumber; }
    public void setBillNumber(String billNumber) { this.billNumber = billNumber; }

    public String getBillType() { return billType; }
    public void setBillType(String billType) { this.billType = billType; }

    public GovInfoBillSponsor getSponsor() { return sponsor; }
    public void setSponsor(GovInfoBillSponsor sponsor) { this.sponsor = sponsor; }

    public List<GovInfoBillCosponsor> getCosponsors() { return cosponsors; }
    public void setCosponsors(List<GovInfoBillCosponsor> cosponsors) {
        this.cosponsors = cosponsors;
        if (cosponsors != null) {
            // Link personIds via dedup lookup (in processor/DAO)
            for (GovInfoBillCosponsor cosponsor : cosponsors) {
                // TODO: Call DAO to set cosponsor.personId based on matchKey
            }
        }
    }

    public List<GovInfoBillAction> getActions() { return actions; }
    public void setActions(List<GovInfoBillAction> actions) { this.actions = actions; }

    public GovInfoBillText getText() { return text; }
    public void setText(GovInfoBillText text) { this.text = text; }

    public List<GovInfoBillCommittee> getCommittees() { return committees; }
    public void setCommittees(List<GovInfoBillCommittee> committees) { this.committees = committees; }

    public List<GovInfoDocRef> getDocRefs() { return docRefs; }
    public void setDocRefs(List<GovInfoDocRef> docRefs) { this.docRefs = docRefs; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GovInfoBill that = (GovInfoBill) o;
        return Objects.equals(congressNumber, that.congressNumber) &&
               Objects.equals(sessionNumber, that.sessionNumber) &&
               Objects.equals(billNumber, that.billNumber) &&
               Objects.equals(billType, that.billType) &&
               Objects.equals(sponsor, that.sponsor) &&
               Objects.equals(cosponsors, that.cosponsors);
    }

    @Override
    public int hashCode() {
        return Objects.hash(congressNumber, sessionNumber, billNumber, billType, sponsor, cosponsors);
    }

    @Override
    public String toString() {
        return "GovInfoBill{" +
                "congressNumber='" + congressNumber + '\'' +
                ", sessionNumber='" + sessionNumber + '\'' +
                ", billNumber='" + billNumber + '\'' +
                ", billType='" + billType + '\'' +
                ", sponsor=" + sponsor +
                ", cosponsors.size=" + (cosponsors != null ? cosponsors.size() : 0) +
                '}';
    }
}
