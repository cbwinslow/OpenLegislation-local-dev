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

    /**
     * Creates a FederalLawXmlFile for the given file and extracts the congressional session and law number from its filename.
     *
     * @param file the federal law XML file
     * @throws IllegalArgumentException if the filename does not contain a valid congress and law number
     */
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

    /**
     * The Congress number parsed from the federal law file's filename.
     *
     * @return the Congress number extracted from the filename
     */
    public int getCongress() {
        return congress;
    }

    /**
     * Gets the law number extracted from the file name.
     *
     * @return the law number extracted from the file name
     */
    public String getLawNumber() {
        return lawNumber;
    }

    /**
     * Obtain the published date and time associated with this federal law XML file.
     *
     * Parses the published date from the filename or the XML header and, if those are not available,
     * falls back to the file's last modified timestamp.
     *
     * @return the published LocalDateTime for this file
     */
    @Override
    public LocalDateTime getPublishedDateTime() {
        // Parse from filename or XML header; fallback to file modified time
        return super.getPublishedDateTime();
    }

    /**
     * Produce a concise string representation of this FederalLawXmlFile including its congress, law number, and file name.
     *
     * @return a string containing the class name and the values of `congress`, `lawNumber`, and `fileName`
     */
    @Override
    public String toString() {
        return "FederalLawXmlFile{" +
                "congress=" + congress +
                ", lawNumber='" + lawNumber + '\'' +
                ", fileName='" + getFileName() + '\'' +
                '}';
    }
}