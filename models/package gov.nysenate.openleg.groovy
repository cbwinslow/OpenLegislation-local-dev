package gov.nysenate.openleg.legislation.bill;

public enum BillActionType {
    UNKNOWN("Unknown"),
    INTRODUCED_HOUSE("Introduced in House"),
    INTRODUCED_SENATE("Introduced in Senate"),
    PASSED_HOUSE("Passed House"),
    PASSED_SENATE("Passed Senate"),
    VETOED("Vetoed"),
    SIGNED("Signed");

    private final String displayText;

    BillActionType(String displayText) {
        this.displayText = displayText;
    }

    public String getDisplayText() {
        return displayText;
    }

    public static BillActionType fromText(String text) {
        if (text != null) {
            text = text.toLowerCase();
            if (text.contains("introduced") && text.contains("house")) return INTRODUCED_HOUSE;
            if (text.contains("introduced") && text.contains("senate")) return INTRODUCED_SENATE;
            if (text.contains("passed") && text.contains("house")) return PASSED_HOUSE;
            if (text.contains("passed") && text.contains("senate")) return PASSED_SENATE;
            if (text.contains("vetoed")) return VETOED;
            if (text.contains("signed")) return SIGNED;
        }
        return UNKNOWN;
    }
}

public class BillAction implements Serializable, Comparable<BillAction> {
    // ... existing fields ...
    private BillActionType type = BillActionType.UNKNOWN;

    public BillAction(LocalDate date, String text, Chamber chamber, int sequenceNo, BillId billId, BillActionType type) {
        // ... existing ...
        this.type = type;
    }

    // Getter/setter
    public BillActionType getType() {
        return type;
    }

    public void setType(BillActionType type) {
        this.type = type;
    }
}
// In mapToBill(), for actions:
String text = actionElem.getElementsByTagName("text").item(0).getTextContent();
BillActionType actionType = BillActionType.fromText(text);
BillAction action = new BillAction(date.atStartOfDay(), actionChamber, text, sequenceNo++, billId, actionType);
bill.actions.add(action);

@Test
public void testMapToBill() throws Exception {
    // ... 
    assertEquals(BillActionType.INTRODUCED_HOUSE, bill.getActions().get(0).getType());
}