package gov.nysenate.openleg.processors.federal;

import gov.nysenate.openleg.dao.federal.FederalCFRDao;
import gov.nysenate.openleg.model.federal.FederalCFR;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.File;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/**
 * Processor for ingesting Code of Federal Regulations (CFR) data from govinfo.gov.
 */
@Component
public class FederalCFRProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalCFRProcessor.class);

    @Autowired
    private FederalCFRDao cfrDao;

    /**
     * Process a CFR XML file and extract section data.
     */
    public List<FederalCFR> processCFRFile(File file) {
        logger.info("Processing CFR file: {}", file.getName());

        List<FederalCFR> sections = new ArrayList<>();

        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(file);

            // Extract CFR sections
            List<FederalCFR> extractedSections = extractCFRSections(doc, file.getName());
            for (FederalCFR section : extractedSections) {
                cfrDao.save(section);
                sections.add(section);
            }

            logger.info("Successfully processed {} CFR sections from: {}", sections.size(), file.getName());

        } catch (Exception e) {
            logger.error("Error processing CFR file: {}", file.getName(), e);
        }

        return sections;
    }

    private List<FederalCFR> extractCFRSections(Document doc, String fileName) {
        List<FederalCFR> sections = new ArrayList<>();

        try {
            Element root = doc.getDocumentElement();

            // Extract title and part information
            Integer title = extractTitle(root);
            Integer part = extractPart(root);
            LocalDate effectiveDate = extractEffectiveDate(root);

            if (title == null || part == null) {
                logger.warn("Missing title or part in CFR file: {}", fileName);
                return sections;
            }

            // Extract all sections
            NodeList sectionNodes = root.getElementsByTagName("section");
            for (int i = 0; i < sectionNodes.getLength(); i++) {
                Element sectionElement = (Element) sectionNodes.item(i);
                FederalCFR section = extractSection(sectionElement, title, part, effectiveDate);
                if (section != null) {
                    sections.add(section);
                }
            }

        } catch (Exception e) {
            logger.error("Error extracting CFR sections from: {}", fileName, e);
        }

        return sections;
    }

    private FederalCFR extractSection(Element sectionElement, Integer title, Integer part, LocalDate effectiveDate) {
        try {
            String sectionNumber = extractSectionNumber(sectionElement);
            String sectionText = extractSectionText(sectionElement);

            if (sectionNumber != null && sectionText != null) {
                FederalCFR cfr = new FederalCFR(title, part, sectionNumber);
                cfr.setSectionText(sectionText);
                cfr.setEffectiveDate(effectiveDate);
                return cfr;
            }

        } catch (Exception e) {
            logger.debug("Could not extract section", e);
        }

        return null;
    }

    private Integer extractTitle(Element root) {
        try {
            NodeList titleNodes = root.getElementsByTagName("title");
            if (titleNodes.getLength() > 0) {
                String titleStr = titleNodes.item(0).getTextContent();
                return Integer.parseInt(titleStr);
            }
        } catch (Exception e) {
            logger.debug("Could not extract title", e);
        }
        return null;
    }

    private Integer extractPart(Element root) {
        try {
            NodeList partNodes = root.getElementsByTagName("part");
            if (partNodes.getLength() > 0) {
                String partStr = partNodes.item(0).getTextContent();
                return Integer.parseInt(partStr);
            }
        } catch (Exception e) {
            logger.debug("Could not extract part", e);
        }
        return null;
    }

    private LocalDate extractEffectiveDate(Element root) {
        try {
            NodeList dateNodes = root.getElementsByTagName("effectiveDate");
            if (dateNodes.getLength() > 0) {
                String dateStr = dateNodes.item(0).getTextContent();
                return LocalDate.parse(dateStr);
            }
        } catch (Exception e) {
            logger.debug("Could not extract effective date", e);
        }
        return null;
    }

    private String extractSectionNumber(Element sectionElement) {
        try {
            // Look for section number in attributes or child elements
            String sectionNum = sectionElement.getAttribute("number");
            if (sectionNum.isEmpty()) {
                NodeList numNodes = sectionElement.getElementsByTagName("sectionNumber");
                if (numNodes.getLength() > 0) {
                    sectionNum = numNodes.item(0).getTextContent();
                }
            }
            return sectionNum;
        } catch (Exception e) {
            logger.debug("Could not extract section number", e);
        }
        return null;
    }

    private String extractSectionText(Element sectionElement) {
        try {
            // Extract all text content from the section
            StringBuilder textBuilder = new StringBuilder();
            NodeList childNodes = sectionElement.getChildNodes();

            for (int i = 0; i < childNodes.getLength(); i++) {
                if (childNodes.item(i).getNodeType() == org.w3c.dom.Node.TEXT_NODE) {
                    textBuilder.append(childNodes.item(i).getTextContent());
                }
            }

            return textBuilder.toString().trim();

        } catch (Exception e) {
            logger.debug("Could not extract section text", e);
        }
        return null;
    }
}