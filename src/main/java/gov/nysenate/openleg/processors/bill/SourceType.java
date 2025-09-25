package gov.nysenate.openleg.processors.bill;

import java.util.Arrays;
import java.util.function.Predicate;
import java.util.regex.Pattern;

/**
 * Enumerates types of {@link SourceFile}s
 */
public enum SourceType {
    XML(".*\\.XML"),
    SOBI("SOBI\\.D\\d{6}\\.T\\d{6}\\.TXT"),
    // Federal collections
    FEDERAL_BILL_XML("federal_bill.*\\.XML"),
    FEDERAL_LAW_XML("federal_law.*\\.XML"),
    FEDERAL_REPORT_XML("federal_report.*\\.XML"),
    FEDERAL_RECORD_XML("federal_record.*\\.XML"),
    FEDERAL_HEARING_XML("federal_hearing.*\\.XML"),
    FEDERAL_CALENDAR_XML("federal_calendar.*\\.XML"),
    FEDERAL_NOMINATION_XML("federal_nomination.*\\.XML"),
    FEDERAL_TREATY_XML("federal_treaty.*\\.XML"),
    FEDERAL_REGISTER_XML("federal_register.*\\.XML"),
    FEDERAL_CFR_XML("federal_cfr.*\\.XML"),
    FEDERAL_STATUTE_XML("federal_statute.*\\.XML");

    private final Predicate<String> filenameMatcher;

    SourceType(String filenameRegex) {
        this.filenameMatcher = Pattern.compile(filenameRegex, Pattern.CASE_INSENSITIVE).asPredicate();
    }

    /* --- Functions --- */

    /**
     * Detects and returns the {@link SourceType} of the given filename.
     * Returns null if the filename does not match any source type patterns
     * @param filename
     * @return {@link SourceType}
     */
    public static SourceType ofFile(String filename) {
        if (filename == null) {
            throw new IllegalArgumentException("Received null filename");
        }
        return Arrays.stream(SourceType.values())
                .filter(sourceType -> sourceType.filenameMatcher.test(filename))
                .findFirst()
                .orElse(null);
    }
}
