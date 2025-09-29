package gov.nysenate.openleg.processors.federal;

import gov.nysenate.openleg.dao.federal.FederalRegisterDao;
import gov.nysenate.openleg.model.federal.FederalRegister;
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
 * Processor for ingesting Federal Register (FR) data from govinfo.gov.
 */
@Component
public class FederalRegisterProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalRegisterProcessor.class);

    @Autowired
    private FederalRegisterDao registerDao;

    /**
     * Process a Federal Register XML file and extract document data.
     */
    public List<FederalRegister> processRegisterFile(File file) {
        logger.info("Processing Federal Register file: {}", file.getName());

        List<FederalRegister> documents = new ArrayList<>();

        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(file);

            // Extract document information
            FederalRegister register = extractRegister(doc, file.getName());
            if (register != null) {
                registerDao.save(register);
                documents.add(register);
                logger.info("Successfully processed register document: {}", register.getDocumentNumber());
            }

        } catch (Exception e) {
            logger.error("Error processing Federal Register file: {}", file.getName(), e);
        }

        return documents;
    }

    private FederalRegister extractRegister(Document doc, String fileName) {
        try {
            Element root = doc.getDocumentElement();

            // Extract basic information
            String documentNumber = extractDocumentNumber(root);
            LocalDate publicationDate = extractPublicationDate(root);
            String title = extractTitle(root);
            String agency = extractAgency(root);
            String documentType = extractDocumentType(root);

            if (documentNumber == null || publicationDate == null) {
                logger.warn("Missing required fields in register document: {}", fileName);
                return null;
            }

            FederalRegister register = new FederalRegister(documentNumber, publicationDate, title);
            register.setAgency(agency);
            register.setDocumentType(documentType);
            register.setAbstractText(extractAbstract(root));
            register.setFullText(extractFullText(root));

            return register;

        } catch (Exception e) {
            logger.error("Error extracting register from: {}", fileName, e);
            return null;
        }
    }

    private String extractDocumentNumber(Element root) {
        try {
            NodeList docNumNodes = root.getElementsByTagName("documentNumber");
            if (docNumNodes.getLength() > 0) {
                return docNumNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract document number", e);
        }
        return null;
    }

    private LocalDate extractPublicationDate(Element root) {
        try {
            NodeList dateNodes = root.getElementsByTagName("publicationDate");
            if (dateNodes.getLength() > 0) {
                String dateStr = dateNodes.item(0).getTextContent();
                return LocalDate.parse(dateStr);
            }
        } catch (Exception e) {
            logger.debug("Could not extract publication date", e);
        }
        return null;
    }

    private String extractTitle(Element root) {
        try {
            NodeList titleNodes = root.getElementsByTagName("title");
            if (titleNodes.getLength() > 0) {
                return titleNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract title", e);
        }
        return "Federal Register Document";
    }

    private String extractAgency(Element root) {
        try {
            NodeList agencyNodes = root.getElementsByTagName("agency");
            if (agencyNodes.getLength() > 0) {
                return agencyNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract agency", e);
        }
        return null;
    }

    private String extractDocumentType(Element root) {
        try {
            NodeList typeNodes = root.getElementsByTagName("documentType");
            if (typeNodes.getLength() > 0) {
                return typeNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract document type", e);
        }
        return "Notice"; // Default
    }

    private String extractAbstract(Element root) {
        try {
            NodeList abstractNodes = root.getElementsByTagName("abstract");
            if (abstractNodes.getLength() > 0) {
                return abstractNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract abstract", e);
        }
        return null;
    }

    private String extractFullText(Element root) {
        try {
            // Extract content from body or main sections
            StringBuilder textBuilder = new StringBuilder();
            NodeList bodyNodes = root.getElementsByTagName("body");

            for (int i = 0; i < bodyNodes.getLength(); i++) {
                Element body = (Element) bodyNodes.item(i);
                textBuilder.append(extractElementText(body)).append("\n\n");
            }

            return textBuilder.toString().trim();

        } catch (Exception e) {
            logger.debug("Could not extract full text", e);
            return "";
        }
    }

    private String extractElementText(Element element) {
        StringBuilder text = new StringBuilder();
        NodeList childNodes = element.getChildNodes();

        for (int i = 0; i < childNodes.getLength(); i++) {
            if (childNodes.item(i).getNodeType() == org.w3c.dom.Node.TEXT_NODE) {
                text.append(childNodes.item(i).getTextContent());
            }
        }

        return text.toString();
    }
}