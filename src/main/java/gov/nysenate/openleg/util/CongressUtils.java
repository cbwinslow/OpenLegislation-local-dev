package gov.nysenate.openleg.util;

public class CongressUtils {

    /**
     * Static method to map federal congress number to session year.
     * For federal bills, session year is the starting year of the congress.
     * e.g., 118th Congress: 2023.
     */
    public static int congressToSessionYear(int congress) {
        if (congress >= 1 && congress <= 117) {
            // Historical approximation: 1789 + (congress - 1) * 2
            return 1789 + (congress - 1) * 2;
        } else if (congress == 118) {
            return 2023;
        } else if (congress == 119) {
            return 2025;
        }
        throw new IllegalArgumentException("Unsupported congress number: " + congress);
    }
}