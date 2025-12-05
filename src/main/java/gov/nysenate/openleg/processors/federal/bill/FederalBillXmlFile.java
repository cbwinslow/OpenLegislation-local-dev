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

    // Pattern: BILLS-119hr1234ih.xml or federal_bill_119_hr_1234.xml
    public static final Pattern FILENAME_PATTERN = Pattern.compile(
            "(?:BILLS-)?(\\d{2,3})([a-zA-Z]{1,4})(\\d+)([a-zA-Z]{0,4})?\\.xml",
            Pattern.CASE_INSENSITIVE
    );

    public FederalBillXmlFile(File file) throws IOException {
        super(file);
        parseFilename(file.getName());
    }

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

    // Getters
    public int getCongress() {
        return congress;
    }

    public String getBillType() {
        return billType;
    }

    public String getBillNumber() {
        return billNumber;
    }

    @Override
    public SourceType getSourceType() {
        return SourceType.FEDERAL_BILL_XML;
    }

    @Override
    public String toString() {
        return "FederalBillXmlFile{" +
                "congress=" + congress +
                ", billType='" + billType + '\'' +
                ", billNumber='" + billNumber + '\'' +
                "} " + super.toString();
    }
}