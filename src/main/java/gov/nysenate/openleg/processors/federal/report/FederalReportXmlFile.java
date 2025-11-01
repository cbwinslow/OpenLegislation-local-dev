package gov.nysenate.openleg.processors.federal.report;

import gov.nysenate.openleg.processors.federal.bill.FederalBillXmlFile;
import gov.nysenate.openleg.processors.bill.XmlFile;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.time.LocalDateTime;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Represents a federal report XML file from govinfo (CRPT collection).
 * Parses filename like "CRPT-119th-HRPT1.xml" to extract congress and reportNumber.
 */
public class FederalReportXmlFile extends XmlFile {

    private static final Logger logger = LoggerFactory.getLogger(FederalReportXmlFile.class);

    private static final Pattern REPORT_PATTERN = Pattern.compile("CRPT-(\\d+)th-(\\w+)PT(\\d+)\\.xml");

    private final int congress;
    private final String reportType; // e.g., HRPT, SRPT
    private final String reportNumber;

    /**
     * Construct a FederalReportXmlFile by parsing the congress number, report type, and report number from the file's name.
     *
     * @param file the XML file from the govinfo CRPT collection; the filename must follow the pattern "CRPT-{congress}th-{type}PT{number}.xml" (e.g. "CRPT-119th-HRPT1.xml")
     * @throws IllegalArgumentException if the file's name does not match the expected pattern
     */
    public FederalReportXmlFile(File file) {
        super(file);
        Matcher matcher = REPORT_PATTERN.matcher(getFileName());
        if (matcher.matches()) {
            congress = Integer.parseInt(matcher.group(1));
            reportType = matcher.group(2);
            reportNumber = matcher.group(3);
        } else {
            throw new IllegalArgumentException("Invalid federal report filename: " + getFileName());
        }
    }

    /**
     * Retrieve the congressional session number parsed from the file name.
     *
     * @return the congress number (for example, `119` for a file named "CRPT-119th-...").
     */
    public int getCongress() {
        return congress;
    }

    /**
     * Gets the report type parsed from the filename (for example, "HRPT" or "SRPT").
     *
     * @return the report type extracted from the filename
     */
    public String getReportType() {
        return reportType;
    }

    /**
     * Gets the report number parsed from the file name.
     *
     * @return the report number extracted from the filename (e.g., 1)
     */
    public String getReportNumber() {
        return reportNumber;
    }

    /**
     * Retrieve the publication date and time associated with this report file.
     *
     * @return the publication LocalDateTime for this report file, or {@code null} if no publication time is available
     */
    @Override
    public LocalDateTime getPublishedDateTime() {
        // Parse from filename or XML header; fallback to file modified time
        return super.getPublishedDateTime();
    }

    /**
     * String representation of this FederalReportXmlFile including congress, report type, report number, and file name.
     *
     * @return a string containing the congress, report type, report number, and file name
     */
    @Override
    public String toString() {
        return "FederalReportXmlFile{" +
                "congress=" + congress +
                ", reportType='" + reportType + '\'' +
                ", reportNumber='" + reportNumber + '\'' +
                ", fileName='" + getFileName() + '\'' +
                '}';
    }
}