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

    /**
 * Creates an empty GovInfoBill instance with all fields unset.
 */
    public GovInfoBill() {}

    /**
     * Create a GovInfoBill populated with its identifying fields and sponsor.
     *
     * Initializes the bill's congressional identifiers and primary sponsor.
     *
     * @param congressNumber the congress number (e.g., "116")
     * @param sessionNumber  the session number within the congress (e.g., "1")
     * @param billNumber     the bill number (e.g., "hr1234")
     * @param billType       the bill type code (e.g., "hr", "s")
     * @param sponsor        the primary sponsor information
     */
    public GovInfoBill(String congressNumber, String sessionNumber, String billNumber, String billType,
                       GovInfoBillSponsor sponsor) {
        this.congressNumber = congressNumber;
        this.sessionNumber = sessionNumber;
        this.billNumber = billNumber;
        this.billType = billType;
        this.sponsor = sponsor;
    }

    /**
 * Gets the Congress number that identifies which Congress the bill belongs to.
 *
 * @return the Congress number string, or {@code null} if not set
 */
    public String getCongressNumber() { return congressNumber; }
    /**
 * Sets the congress number that identifies the congressional term for this bill.
 *
 * @param congressNumber the congress number (for example, "118")
 */
public void setCongressNumber(String congressNumber) { this.congressNumber = congressNumber; }

    /**
 * Returns the session number of the bill.
 *
 * @return the session number
 */
public String getSessionNumber() { return sessionNumber; }
    /**
 * Set the session number for this bill.
 */
public void setSessionNumber(String sessionNumber) { this.sessionNumber = sessionNumber; }

    /**
 * Gets the bill number used to identify this bill within its congressional session.
 *
 * @return the bill number identifying the bill within the session
 */
public String getBillNumber() { return billNumber; }
    /**
 * Set the bill's identifying number within the session.
 *
 * @param billNumber the bill number identifier (for example "H1234" or "S56")
 */
public void setBillNumber(String billNumber) { this.billNumber = billNumber; }

    /**
 * The bill type identifier for this bill (for example, "hr" or "s").
 *
 * @return the bill type identifier, or {@code null} if not set
 */
public String getBillType() { return billType; }
    /**
 * Set the bill type code for this bill.
 *
 * @param billType the bill type code (for example, "hr" or "s")
 */
public void setBillType(String billType) { this.billType = billType; }

    /**
 * The primary sponsor of the bill.
 *
 * @return the bill's primary sponsor, or {@code null} if not set
 */
public GovInfoBillSponsor getSponsor() { return sponsor; }
    /**
 * Sets the primary sponsor of this bill.
 *
 * @param sponsor the sponsor to assign, or {@code null} to clear the sponsor
 */
public void setSponsor(GovInfoBillSponsor sponsor) { this.sponsor = sponsor; }

    /**
 * Gets the cosponsors for the bill.
 *
 * @return the list of cosponsors, or {@code null} if not set
 */
public List<GovInfoBillCosponsor> getCosponsors() { return cosponsors; }
    /**
     * Set the list of cosponsors for this bill and attempt to associate each cosponsor with a deduplicated person ID.
     *
     * If the provided list is non-null, each cosponsor will be processed so its `personId` can be populated via a deduplication lookup (DAO integration is currently a TODO).
     *
     * @param cosponsors the list of cosponsors to assign to this bill; may be null
     */
    public void setCosponsors(List<GovInfoBillCosponsor> cosponsors) { 
        this.cosponsors = cosponsors; 
        if (cosponsors != null) {
            // Link personIds via dedup lookup (in processor/DAO)
            for (GovInfoBillCosponsor cosponsor : cosponsors) {
                // TODO: Call DAO to set cosponsor.personId based on matchKey
            }
        }
    }

    /**
 * Retrieves the actions recorded for this bill.
 *
 * @return the list of {@link GovInfoBillAction} objects associated with this bill, or {@code null} if none
 */
public List<GovInfoBillAction> getActions() { return actions; }
    /**
 * Set the list of legislative actions associated with this bill.
 *
 * @param actions the bill's legislative actions; may be null to clear the current list
 */
public void setActions(List<GovInfoBillAction> actions) { this.actions = actions; }

    /**
 * Retrieve the bill's parsed text representation.
 *
 * @return the {@link GovInfoBillText} containing the bill's text, or {@code null} if none is set
 */
public GovInfoBillText getText() { return text; }
    /**
 * Set the bill's parsed text representation.
 *
 * @param text the GovInfoBillText for this bill, or null to clear the current text
 */
public void setText(GovInfoBillText text) { this.text = text; }

    /**
 * Get the committees associated with this bill.
 *
 * @return the list of committees for the bill, or {@code null} if none are set
 */
public List<GovInfoBillCommittee> getCommittees() { return committees; }
    /**
 * Set the committees associated with this bill.
 *
 * @param committees the list of GovInfoBillCommittee objects representing the bill's committees
 */
public void setCommittees(List<GovInfoBillCommittee> committees) { this.committees = committees; }

    /**
 * Document references associated with this bill.
 *
 * @return the list of document references for the bill, or {@code null} if not set
 */
public List<GovInfoDocRef> getDocRefs() { return docRefs; }
    /**
 * Set the list of document references associated with this bill.
 *
 * @param docRefs the GovInfo document references for the bill, or null to clear
 */
public void setDocRefs(List<GovInfoDocRef> docRefs) { this.docRefs = docRefs; }

    /**
     * Determines whether this GovInfoBill is equal to the specified object.
     *
     * @param o the object to compare with this GovInfoBill
     * @return {@code true} if the object is a GovInfoBill and its congressNumber, sessionNumber,
     *         billNumber, billType, sponsor, and cosponsors are equal to those of this instance;
     *         {@code false} otherwise.
     */
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

    /**
     * Compute a hash code for this GovInfoBill using its identifying fields and sponsor/cosponsors.
     *
     * @return the hash code derived from congressNumber, sessionNumber, billNumber, billType, sponsor, and cosponsors
     */
    @Override
    public int hashCode() {
        return Objects.hash(congressNumber, sessionNumber, billNumber, billType, sponsor, cosponsors);
    }

    /**
     * Build a concise single-line representation of the bill including key identifiers, sponsor, and cosponsor count.
     *
     * @return a string containing congressNumber, sessionNumber, billNumber, billType, sponsor, and the number of cosponsors
     */
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