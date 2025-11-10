package gov.nysenate.openleg.model.federal;

/**
 * Enumeration representing the chambers of the United States Congress.
 */
public enum FederalChamber {
    HOUSE("House of Representatives"),
    SENATE("Senate"),
    JOINT("Joint Committee");

    private final String displayName;

    FederalChamber(String displayName) {
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }

    public static FederalChamber fromString(String chamber) {
        if (chamber == null) return null;
        String upper = chamber.toUpperCase();
        return switch (upper) {
            case "HOUSE", "H", "REPRESENTATIVES" -> HOUSE;
            case "SENATE", "S" -> SENATE;
            case "JOINT", "J" -> JOINT;
            default -> null;
        };
    }

    @Override
    public String toString() {
        return displayName;
    }
}