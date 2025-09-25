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

    public int getCongress() {
        return congress;
    }

    public String getReportType() {
        return reportType;
    }

    public String getReportNumber() {
        return reportNumber;
    }

    @Override
    public LocalDateTime getPublishedDateTime() {
        // Parse from filename or XML header; fallback to file modified time
        return super.getPublishedDateTime();
    }

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