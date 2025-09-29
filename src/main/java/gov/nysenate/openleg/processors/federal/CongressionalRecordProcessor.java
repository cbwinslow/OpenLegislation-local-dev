package gov.nysenate.openleg.processors.federal;

import gov.nysenate.openleg.dao.federal.FederalTranscriptDao;
import gov.nysenate.openleg.model.federal.FederalChamber;
import gov.nysenate.openleg.model.federal.FederalTranscript;
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
 * Processor for ingesting Congressional Record (CREC) data from govinfo.gov.
 */
@Component
public class CongressionalRecordProcessor {

    private static final Logger logger = LoggerFactory.getLogger(CongressionalRecordProcessor.class);

    @Autowired
    private FederalTranscriptDao transcriptDao;

    /**
     * Process a Congressional Record XML file and extract transcript data.
     */
    public List<FederalTranscript> processTranscriptFile(File file) {
        logger.info("Processing Congressional Record file: {}", file.getName());

        List<FederalTranscript> transcripts = new ArrayList<>();

        try {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            DocumentBuilder builder = factory.newDocumentBuilder();
            Document doc = builder.parse(file);

            // Extract transcript information
            FederalTranscript transcript = extractTranscript(doc, file.getName());
            if (transcript != null) {
                transcriptDao.save(transcript);
                transcripts.add(transcript);
                logger.info("Successfully processed transcript: {}", transcript.getTranscriptId());
            }

        } catch (Exception e) {
            logger.error("Error processing Congressional Record file: {}", file.getName(), e);
        }

        return transcripts;
    }

    private FederalTranscript extractTranscript(Document doc, String fileName) {
        try {
            Element root = doc.getDocumentElement();

            // Extract basic information
            String transcriptId = extractTranscriptId(fileName);
            Integer congress = extractCongress(root);
            LocalDate date = extractDate(root);
            Integer volume = extractVolume(root);
            String title = extractTitle(root);
            FederalChamber chamber = extractChamber(root);

            if (transcriptId == null || congress == null || date == null) {
                logger.warn("Missing required fields in transcript: {}", fileName);
                return null;
            }

            FederalTranscript transcript = new FederalTranscript(transcriptId, congress, date);
            transcript.setVolume(volume);
            transcript.setTitle(title);
            transcript.setChamber(chamber);
            transcript.setTranscriptText(extractTranscriptText(root));

            return transcript;

        } catch (Exception e) {
            logger.error("Error extracting transcript from: {}", fileName, e);
            return null;
        }
    }

    private String extractTranscriptId(String fileName) {
        // Extract from filename: CREC-2025-01-03-pt1.xml -> CREC-2025-01-03
        if (fileName.startsWith("CREC-") && fileName.endsWith(".xml")) {
            return fileName.substring(0, fileName.length() - 4).replace("-pt1", "").replace("-pt2", "");
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
            logger.warn("Could not extract congress from transcript");
        }
        return null;
    }

    private LocalDate extractDate(Element root) {
        try {
            NodeList dateNodes = root.getElementsByTagName("date");
            if (dateNodes.getLength() > 0) {
                String dateStr = dateNodes.item(0).getTextContent();
                return LocalDate.parse(dateStr);
            }
        } catch (Exception e) {
            logger.warn("Could not extract date from transcript");
        }
        return null;
    }

    private Integer extractVolume(Element root) {
        try {
            NodeList volumeNodes = root.getElementsByTagName("volume");
            if (volumeNodes.getLength() > 0) {
                return Integer.parseInt(volumeNodes.item(0).getTextContent());
            }
        } catch (Exception e) {
            logger.warn("Could not extract volume from transcript");
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
            logger.warn("Could not extract title from transcript");
        }
        return "Congressional Record";
    }

    private FederalChamber extractChamber(Element root) {
        try {
            NodeList chamberNodes = root.getElementsByTagName("chamber");
            if (chamberNodes.getLength() > 0) {
                String chamberStr = chamberNodes.item(0).getTextContent();
                return FederalChamber.fromString(chamberStr);
            }
        } catch (Exception e) {
            logger.warn("Could not extract chamber from transcript");
        }
        return FederalChamber.SENATE; // Default
    }

    private String extractTranscriptText(Element root) {
        try {
            // Extract all speech content
            StringBuilder textBuilder = new StringBuilder();
            NodeList speechNodes = root.getElementsByTagName("speech");

            for (int i = 0; i < speechNodes.getLength(); i++) {
                Element speech = (Element) speechNodes.item(i);
                String speaker = extractSpeaker(speech);
                String content = extractSpeechContent(speech);

                if (speaker != null && content != null) {
                    textBuilder.append(speaker).append(": ").append(content).append("\n\n");
                }
            }

            return textBuilder.toString().trim();

        } catch (Exception e) {
            logger.warn("Could not extract transcript text", e);
            return "";
        }
    }

    private String extractSpeaker(Element speech) {
        try {
            NodeList speakerNodes = speech.getElementsByTagName("speaker");
            if (speakerNodes.getLength() > 0) {
                return speakerNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract speaker", e);
        }
        return null;
    }

    private String extractSpeechContent(Element speech) {
        try {
            NodeList contentNodes = speech.getElementsByTagName("text");
            if (contentNodes.getLength() > 0) {
                return contentNodes.item(0).getTextContent();
            }
        } catch (Exception e) {
            logger.debug("Could not extract speech content", e);
        }
        return null;
    }
}