package gov.nysenate.openleg.processors.federal;

import gov.nysenate.openleg.dao.federal.FederalHearingDao;
import gov.nysenate.openleg.model.federal.FederalChamber;
import gov.nysenate.openleg.model.federal.FederalHearing;
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
 * Processor for ingesting Federal Hearing (CHRG) data from govinfo.gov.
 */
@Component
public class FederalHearingProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalHearingProcessor.class);

    @Autowired
    private FederalHearingDao hearingDao;

    /**
     * Process a Federal Hearing XML file and extract hearing data.
     */
    public List<FederalHearing> processHearingFile(File file) {
        logger.info("Processing Federal Hearing file: {}", file.getName());

        List<FederalHearing> hearings = new ArrayList<>();

        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(file);

            // Extract hearing information
            FederalHearing hearing = extractHearing(doc, file.getName());
            if (hearing != null) {
                hearingDao.save(hearing);
                hearings.add(hearing);
                logger.info("Successfully processed hearing: {}", hearing.getHearingId());
            }

        } catch (Exception e) {
            logger.error("Error processing Federal Hearing file: {}", file.getName(), e);
        }

        return hearings;
    }

    private FederalHearing extractHearing(Document doc, String fileName) {
        try {
            Element root = doc.getDocumentElement();

            // Extract basic information
            String hearingId = extractHearingId(fileName);
            Integer congress = extractCongress(root);
            String title = extractTitle(root);
            LocalDate hearingDate = extractHearingDate(root);
            String committeeName = extractCommitteeName(root);
            FederalChamber chamber = extractChamber(root);
            String hearingType = extractHearingType(root);
            String location = extractLocation(root);

            if (hearingId == null || congress == null) {
                logger.warn("Missing required fields in hearing: {}", fileName);
                return null;
            }

            FederalHearing hearing = new FederalHearing(hearingId, congress, title);
            hearing.setHearingDate(hearingDate);
            hearing.setCommitteeName(committeeName);
            hearing.setChamber(chamber);
            hearing.setHearingType(hearingType);
            hearing.setLocation(location);
            hearing.setTranscriptText(extractTranscriptText(root));

            return hearing;

        } catch (Exception e) {
            logger.error("Error extracting hearing from: {}", fileName, e);
            return null;
        }
    }

    private String extractHearingId(String fileName) {
        // Extract from filename: CHRG-119hhrg12345.xml -> CHRG-119hhrg12345
        if (fileName.startsWith("CHRG-") && fileName.endsWith(".xml")) {
            return fileName.substring(0, fileName.length() - 4);
        }
        return null;
    }

    private Integer extractCongress(Element root) {
        try {
            NodeList congressNodes = root.getElementsByTagName("congress");
            if (congressNodes.getLength() > 0) {
                return Integer.parseInt(congressNodes.item(0).getTextContent());
            }
        } catch (Exception e) {
            logger.debug("Could not extract congress from hearing");
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
            logger.debug("Could not extract title from hearing");
        }
        return "Federal Hearing";
    }

    private LocalDate extractHearingDate(Element root) {
        try {
            NodeList dateNodes = root.getElementsByTagName("hearingDate");
            if (dateNodes.getLength() > 0) {
                String dateStr = dateNodes.item(0).getTextContent();
                return LocalDate.parse(dateStr);
            }
        } catch (Exception e) {
            logger.debug("Could not extract hearing date");
        }
        return null;
    }

    private String extractCommitteeName(Element root) {
        try {
            NodeList committeeNodes = root.getElementsByTagName("committee");
            if (committeeNodes.getLength() > 0) {
                Element committee = (Element) committeeNodes.item(0);
                NodeList nameNodes = committee.getElementsByTagName("name");
                if (nameNodes.getLength() > 0) {
                    return nameNodes.item(0).getTextContent();
                }
            }
        } catch (Exception e) {
            logger.debug("Could not extract committee name");
        }
        return null;
    }

    private FederalChamber extractChamber(Element root) {
        try {
            NodeList chamberNodes = root.getElementsByTagName("chamber");
            if (chamberNodes.getLength() > 0) {
                String chamberStr = chamberNodes.item(0).getTextContent();
                return FederalChamber.fromString(chamberStr);
            }
        } catch (Exception e) {
            logger.debug("Could not extract chamber from hearing");
        }
        return FederalChamber.SENATE; // Default
    }

    private String extractHearingType(Element root) {
        try {
            NodeList typeNodes = root.getElementsByTagName("hearingType");
            if (typeNodes.getLength() > 0) {
                return typeNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract hearing type");
        }
        return "Legislative";
    }

    private String extractLocation(Element root) {
        try {
            NodeList locationNodes = root.getElementsByTagName("location");
            if (locationNodes.getLength() > 0) {
                return locationNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract location");
        }
        return null;
    }

    private String extractTranscriptText(Element root) {
        try {
            // Extract witness testimony and discussion
            StringBuilder textBuilder = new StringBuilder();
            NodeList witnessNodes = root.getElementsByTagName("witness");

            for (int i = 0; i < witnessNodes.getLength(); i++) {
                Element witness = (Element) witnessNodes.item(i);
                String name = extractWitnessName(witness);
                String testimony = extractWitnessTestimony(witness);

                if (name != null && testimony != null) {
                    textBuilder.append("Witness: ").append(name).append("\n");
                    textBuilder.append("Testimony: ").append(testimony).append("\n\n");
                }
            }

            return textBuilder.toString().trim();

        } catch (Exception e) {
            logger.debug("Could not extract transcript text", e);
            return "";
        }
    }

    private String extractWitnessName(Element witness) {
        try {
            NodeList nameNodes = witness.getElementsByTagName("name");
            if (nameNodes.getLength() > 0) {
                return nameNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract witness name", e);
        }
        return null;
    }

    private String extractWitnessTestimony(Element witness) {
        try {
            NodeList testimonyNodes = witness.getElementsByTagName("testimony");
            if (testimonyNodes.getLength() > 0) {
                return testimonyNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract witness testimony", e);
        }
        return null;
    }
}