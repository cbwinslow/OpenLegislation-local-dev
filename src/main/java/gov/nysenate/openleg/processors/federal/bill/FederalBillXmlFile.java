package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.processors.bill.xml.XmlFile;
import gov.nysenate.openleg.processors.bill.SourceType;
import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Represents a federal bill XML file from congress.gov or govinfo.gov.
 * Parses filename for congress number, bill type, number, and published date.
 */
public class FederalBillXmlFile extends XmlFile {

    private int congress;
    private String billType; // e.g., "hr", "s"
    private String billNumber;


        Pattern.CASE_INSENSITIVE
    );

    /**
     * Creates a FederalBillXmlFile from the given file and extracts congress, bill type, and bill number from its filename.
     *
     * @param file the XML file representing a federal bill; its name must match the expected federal bill filename pattern
     * @throws IOException if an I/O error occurs while initializing the underlying XmlFile
     * @throws IllegalArgumentException if the filename does not match the expected federal bill pattern
     */
    public FederalBillXmlFile(File file) throws IOException {
        super(file);
        parseFilename(file.getName());
    }

    /**
     * Parses a federal bill filename and sets the congress, billType, and billNumber fields.
     *
     * @param fileName the filename to parse; must match the class's FILENAME_PATTERN
     * @throws IllegalArgumentException if the filename does not match the expected federal bill format
     */
    private void parseFilename(String fileName) {
        Matcher matcher = FILENAME_PATTERN.matcher(fileName);
        if (matcher.matches()) {
            congress = Integer.parseInt(matcher.group(2));
            billType = matcher.group(3) != null ? matcher.group(3).toUpperCase() : "";
            billNumber = matcher.group(4) != null ? matcher.group(4) : "";
        } else {
            throw new IllegalArgumentException("Invalid federal bill filename: " + fileName);
        }
    }

    /**
     * Provides the congress number parsed from the file's filename.
     *
     * @return the congress number extracted from the filename
     */
    public int getCongress() {
        return congress;
    }

    /**
     * Returns the bill type parsed from the filename (for example "HR" or "S"), or an empty string if no type was present.
     *
     * @return the bill type in uppercase when present, or an empty string if absent
     */
    public String getBillType() {
        return billType;
    }

    /**
     * Gets the bill number parsed from the filename.
     *
     * @return the bill number parsed from the filename, or an empty string if no bill number was present
     */
    public String getBillNumber() {
        return billNumber;
    }

    /**
     * Identifies the source type for this file variant.
     *
     * @return `SourceType.FEDERAL_BILL_XML` indicating the file represents a federal bill XML.
     */
    @Override
    public SourceType getSourceType() {
        return SourceType.FEDERAL_BILL_XML;
    }

    /**
     * Produce a string representation of the FederalBillXmlFile including parsed congress, bill type, and bill number.
     *
     * @return the string containing the parsed congress, bill type, and bill number followed by the superclass representation
     */
    @Override
    public String toString() {
        return "FederalBillXmlFile{" +
                "congress=" + congress +
                ", billType='" + billType + '\'' +
                ", billNumber='" + billNumber + '\'' +
                "} " + super.toString();
    }
}