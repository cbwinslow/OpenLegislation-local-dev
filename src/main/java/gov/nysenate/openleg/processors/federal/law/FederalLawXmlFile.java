package gov.nysenate.openleg.processors.federal.law;

import gov.nysenate.openleg.processors.federal.bill.FederalBillXmlFile;
import gov.nysenate.openleg.processors.bill.XmlFile;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.time.LocalDateTime;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Represents a federal law XML file from govinfo (PLAW collection).
 * Parses filename like "PLAW-119publ1.xml" to extract congress and lawNumber.
 */
public class FederalLawXmlFile extends XmlFile {

    private static final Logger logger = LoggerFactory.getLogger(FederalLawXmlFile.class);

    private static final Pattern LAW_PATTERN = Pattern.compile("PLAW-(\\d+)publ(\\d+)\\.xml");

    private final int congress;
    private final String lawNumber;

    public FederalLawXmlFile(File file) {
        super(file);
        Matcher matcher = LAW_PATTERN.matcher(getFileName());
        if (matcher.matches()) {
            congress = Integer.parseInt(matcher.group(1));
            lawNumber = matcher.group(2);
        } else {
            throw new IllegalArgumentException("Invalid federal law filename: " + getFileName());
        }
    }

    public int getCongress() {
        return congress;
    }

    public String getLawNumber() {
        return lawNumber;
    }

    @Override
    public LocalDateTime getPublishedDateTime() {
        // Parse from filename or XML header; fallback to file modified time
        return super.getPublishedDateTime();
    }

    @Override
    public String toString() {
        return "FederalLawXmlFile{" +
                "congress=" + congress +
                ", lawNumber='" + lawNumber + '\'' +
                ", fileName='" + getFileName() + '\'' +
                '}';
    }
}