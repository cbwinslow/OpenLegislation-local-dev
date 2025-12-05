package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.common.util.XmlHelper;
import gov.nysenate.openleg.config.annotation.UnitTest;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import org.junit.Before;
import org.junit.Test;
import org.junit.experimental.categories.Category;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import static org.junit.Assert.*;

/**
 * Unit test for FederalBillXmlProcessor.
 * Note: Full integration tests that exercise the process() method would require
 * Spring context initialization and are better placed in integration test suites.
 */
@Category(UnitTest.class)
public class FederalBillXmlProcessorTest {

    @Mock
    private XmlHelper xmlHelper;

    private FederalBillXmlProcessor processor;

    @Before
    public void setup() {
        MockitoAnnotations.openMocks(this);
        processor = new FederalBillXmlProcessor(xmlHelper);
    }

    @Test
    public void testGetSupportedType() {
        assertEquals(LegDataFragmentType.BILL, processor.getSupportedType());
    }
}