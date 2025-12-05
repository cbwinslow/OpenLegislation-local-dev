package gov.nysenate.openleg.processors.federal.law;

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
 * Represents a federal law XML file from govinfo (PLAW collection).
 * Parses filename like "PLAW-119publ1.xml" to extract congress and lawNumber.
 */
public class FederalLawXmlFile extends XmlFile {

    private static final Logger logger = LoggerFactory.getLogger(FederalLawXmlFile.class);

    private static final Pattern LAW_PATTERN = Pattern.compile("PLAW-(\\d+)publ(\\d+)\\.xml");

    private final int congress;
    private final String lawNumber;

    /**
     * Constructs a FederalLawXmlFile by validating and parsing the filename to extract congress and law number.
     *
     * @param file the XML file representing a federal law
     * @throws IOException if an I/O error occurs during file handling
     * @throws IllegalArgumentException if the filename does not match the expected federal law pattern
     */
    public FederalLawXmlFile(File file) throws IOException {
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
     * Retrieve the Congress number parsed from the file's PLAW filename.
     *
     * @return the Congress number extracted from the filename
     */
    public int getCongress() {
        return congress;
    }

    /**
     * Retrieves the law number parsed from the XML file's filename.
     *
     * @return the law number extracted from the filename
     */
    public String getLawNumber() {
        return lawNumber;
    }

    /**
     * Get the published date and time for this federal law XML file.
     *
     * Attempts to determine the published date/time from the filename or the XML header; if neither provides a value,
     * the file's last modified time is used as a fallback.
     *
     * @return the published {@link java.time.LocalDateTime} for the file, determined from filename or XML header with fallback to the file's last modified time
     */
    @Override
    public LocalDateTime getPublishedDateTime() {
        // Parse from filename or XML header; fallback to file modified time
        return super.getPublishedDateTime();
    }

    /**
     * String representation of the FederalLawXmlFile including congress, law number, and file name.
     *
     * @return a string containing the class name and the congress, law number, and file name
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