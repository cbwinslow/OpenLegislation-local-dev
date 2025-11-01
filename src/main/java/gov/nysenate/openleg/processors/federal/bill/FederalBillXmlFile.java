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

    private static final Pattern FILENAME_PATTERN = Pattern.compile(
        "(BILLS?|BILLSTATUS?|BILL-SUMMARIES?)-(\\d{3})thCongress(?:-(HR|S|HJ| SJ|HConRes|SConRes|HJRes|SJRes))?(\\d+)?\\.xml",
        Pattern.CASE_INSENSITIVE
    );

    /**
     * Creates a FederalBillXmlFile for the given file and parses its filename to extract
     * the congress number, bill type, and bill number.
     *
     * @param file the XML file to represent; its filename will be parsed for metadata
     * @throws IOException if an I/O error occurs while initializing the underlying XmlFile
     */
    public FederalBillXmlFile(File file) throws IOException {
        super(file);
        parseFilename(file.getName());
    }

    /**
     * Parse the federal bill filename and populate the congress, billType, and billNumber fields.
     *
     * If the filename matches the expected pattern, sets:
     * - congress to the parsed 3-digit congress number,
     * - billType to the uppercased bill type or an empty string if absent,
     * - billNumber to the parsed bill number or an empty string if absent.
     *
     * @param fileName the filename to parse
     * @throws IllegalArgumentException if the filename does not match the expected federal bill pattern
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
     * Get the congress number parsed from the file name.
     *
     * @return the congress number extracted from the filename
     */
    public int getCongress() {
        return congress;
    }

    /**
     * The bill type parsed from the filename.
     *
     * @return the bill type in uppercase (e.g., "HR", "S"), or an empty string if no type was present in the filename
     */
    public String getBillType() {
        return billType;
    }

    /**
     * The bill number parsed from the file name.
     *
     * @return the bill number parsed from the filename, or an empty string if not present
     */
    public String getBillNumber() {
        return billNumber;
    }

    /**
     * Provides the SourceType for federal bill XML files.
     *
     * @return the source type SourceType.FEDERAL_BILL_XML
     */
    @Override
    public SourceType getSourceType() {
        return SourceType.FEDERAL_BILL_XML;
    }

    /**
     * String representation including the parsed congress number, bill type, bill number, and superclass file info.
     *
     * @return a string containing the congress number, bill type, bill number, and the superclass's string representation
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