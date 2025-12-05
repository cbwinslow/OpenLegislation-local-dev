package gov.nysenate.openleg.processors.federal.bill;


import gov.nysenate.openleg.legislation.SessionYear;
import gov.nysenate.openleg.legislation.bill.*;
import gov.nysenate.openleg.legislation.committee.Chamber;
import gov.nysenate.openleg.legislation.member.Member;
import gov.nysenate.openleg.legislation.member.Person;
import gov.nysenate.openleg.legislation.member.PersonName;
import gov.nysenate.openleg.legislation.member.SessionMember;
import gov.nysenate.openleg.processors.ParseError;
import gov.nysenate.openleg.processors.bill.LegDataFragment;
import gov.nysenate.openleg.processors.bill.LegDataFragmentType;
import gov.nysenate.openleg.processors.bill.AbstractBillProcessor;

import org.springframework.stereotype.Service;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

import javax.xml.xpath.XPathExpressionException;

import java.io.IOException;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * Processor for federal bill XML from congress.gov/govinfo.
 * Parses XML to Bill model using DOM parsing.
 */
@Service
public class FederalBillXmlProcessor extends AbstractBillProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalBillXmlProcessor.class);

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd");


    }

    /**
     * Indicates this processor handles bill data fragments.
     *
     * @return the supported fragment type, LegDataFragmentType.BILL
     */
    @Override
    public LegDataFragmentType getSupportedType() {
        return LegDataFragmentType.BILL;
    }

    /**
         * Processes a federal bill data fragment by parsing its XML and producing the corresponding Bill model.
         *
         * @param fragment the LegDataFragment containing the federal bill XML to be parsed and converted
         */
        @Override
    public void process(LegDataFragment fragment) {

        }
        BillText billText = new BillText(textBuilder.toString());
        amendment.setBillText(billText);



        bill.setFederalCongress(congress);
        bill.setFederalSource("govinfo");
        
        return bill;
    }
    
    /**
     * Retrieve the text content of the first descendant element with the specified tag name.
     *
     * @param parent the element to search within
     * @param tagName the tag name to match
     * @return the text content of the first matching element, or {@code null} if no match is found
     */
    private String getElementTextContent(Element parent, String tagName) {
        NodeList nodeList = parent.getElementsByTagName(tagName);
        if (nodeList.getLength() > 0) {
            return nodeList.item(0).getTextContent();
        }
        return null;
    }

    /**
     * Retrieve the text content of the first child element with the given tag name.
     *
     * @param parent  the parent Element to search within
     * @param tagName the child element tag name to find
     * @return the text content of the first matching child element, or {@code null} if none is found
     */
    private String getElementText(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent();
        }
        return null;
    }

    /**
     * Convert a U.S. Congress ordinal to the calendar year when its first session begins.
     *
     * @param congress the ordinal number of the U.S. Congress (e.g., 119)
     * @return the starting year of that Congress's first session (e.g., 119 -> 2025)
     */
    private int congressToSessionYear(int congress) {
        return 1789 + (congress - 1) * 2; // Starting year of congress, e.g., 119th = 2025
    }
    */

    /**
     * Retrieves the text content of the first child element with the specified tag name.
     *
     * @param parent  the element to search within
     * @param tagName the name of the child element whose text content is returned
     * @return the text content of the first matching child element, or an empty string if no such element exists
     */
    private String getElementText(Element parent, String tagName) {
        NodeList nodes = parent.getElementsByTagName(tagName);
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent();
        }
        return "";
    }
}