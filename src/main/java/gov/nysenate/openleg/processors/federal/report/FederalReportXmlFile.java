package gov.nysenate.openleg.processors.federal.report;

import gov.nysenate.openleg.processors.federal.bill.FederalBillXmlFile;
import gov.nysenate.openleg.processors.bill.xml.XmlFile;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
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
     * Creates a FederalReportXmlFile by parsing the congress number, report type, and report number from the file's name.
     *
     * The filename must match the pattern "CRPT-<congress>th-<TYPE>PT<NUMBER>.xml"; on success the parsed values are stored
     * in the instance fields `congress`, `reportType`, and `reportNumber`.
     *
     * @param file the XML file representing a federal report
     * @throws IOException if an I/O error occurs while initializing the underlying XmlFile
     * @throws IllegalArgumentException if the filename does not match the expected federal report format
     */
    public FederalReportXmlFile(File file) throws IOException {
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
     * Returns the congressional session number extracted from the file name.
     *
     * @return the congress number parsed from the filename
     */
    public int getCongress() {
        return congress;
    }

    /**
     * Provide the report type extracted from the filename.
     *
     * @return the report type extracted from the filename (e.g., HRPT, SRPT)
     */
    public String getReportType() {
        return reportType;
    }

    /**
     * Retrieves the report number extracted from the filename.
     *
     * @return the report number string parsed from the filename
     */
    public String getReportNumber() {
        return reportNumber;
    }

    /**
     * Determine the published date and time for this federal report.
     *
     * Parses the date/time from the filename or the XML header; if neither is present,
     * falls back to the file's last modified time.
     *
     * @return the published {@link java.time.LocalDateTime} for the report, or the file's
     *         last modified time when a published date is not available
     */
    @Override
    public LocalDateTime getPublishedDateTime() {
        // Parse from filename or XML header; fallback to file modified time
        return super.getPublishedDateTime();
    }

    /**
     * Produce a compact string representation of this FederalReportXmlFile including congress, report type,
     * report number, and file name.
     *
     * @return a string containing the congress, report type, report number, and file name for debugging/logging
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