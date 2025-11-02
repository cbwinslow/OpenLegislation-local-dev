package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import org.junit.Before;
import org.junit.Test;


import static org.junit.Assert.*;

/**
 * Unit test for FederalBillXmlProcessor.
 * Note: Full integration tests that exercise the process() method would require
 * Spring context initialization and are better placed in integration test suites.
 */
public class FederalBillXmlProcessorTest {

    private FederalBillXmlProcessor processor;

    @Before
    public void setup() {
        processor = new FederalBillXmlProcessor();
    }

    @Test
    public void testGetSupportedType() {
        assertEquals(LegDataFragmentType.BILL, processor.getSupportedType());
    }


}