package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import org.junit.Before;
import org.junit.Test;
import org.w3c.dom.Document;
import org.xml.sax.SAXException;

import javax.xml.parsers.ParserConfigurationException;
import java.io.File;
import java.time.LocalDateTime;

import static org.junit.Assert.*;

/**
 * Unit test for FederalBillXmlProcessor mapping.
 */
public class FederalBillXmlProcessorTest {

    private FederalBillXmlProcessor processor;

    private FederalBillXmlFile testFile;

    @Before
    public void setup() {
        processor = new FederalBillXmlProcessor();
        File xmlFile = new File("src/test/resources/federal-samples/bills/BILLS-119th-HR1.xml");
        testFile = new FederalBillXmlFile(xmlFile);
        testFile.setPublishedDateTime(LocalDateTime.now());
    }

    @Test
    public void testGetSupportedType() {
        assertEquals(LegDataFragmentType.BILL, processor.getSupportedType());
    }

    @Test
    public void testMapToBill() throws ParserConfigurationException, SAXException, IOException {
        Document doc = processor.parseXml(testFile.getFile());
        Bill bill = processor.mapToBill(doc, testFile);

        assertNotNull(bill);
        assertEquals("1", bill.getBaseBillId().getPrintNo());
        assertEquals(2025, bill.getBaseBillId().getSession().year());
        assertEquals("To provide for the establishment of a White House Conference on Rural Health.", bill.getTitle());
        assertEquals(1, bill.getSponsors().size());
        assertTrue(bill.getSponsors().get(0).getMember().getName().contains("John Doe"));
        assertEquals(1, bill.getActions().size());
        assertEquals("Introduced in House", bill.getActions().get(0).getText());
        assertNotNull(bill.getText());
        assertTrue(bill.getText().getBaseText().contains("Short title"));
    }

    @Test(expected = ParseError.class)
    public void testProcessInvalidXml() throws Exception {
        File invalidFile = new File("nonexistent.xml");
        processor.parseXml(invalidFile); // Throws
    }
}
