package gov.nysenate.openleg.service;

import gov.nysenate.openleg.db.repository.*;
import gov.nysenate.openleg.ingestion.model.GovinfoBill;
import gov.nysenate.openleg.model.db.DbAction;
import gov.nysenate.openleg.model.db.DbAmendment;
import gov.nysenate.openleg.model.db.DbBill;
import gov.nysenate.openleg.model.db.DbSponsor;
import gov.nysenate.openleg.util.CongressUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Comparator;

@Service
public class IngestionService {

    private static final Logger logger = LoggerFactory.getLogger(IngestionService.class);

    private final BillRepository billRepository;
    private final SponsorRepository sponsorRepository;
    private final ActionRepository actionRepository;
    private final CommitteeRepository committeeRepository;
    private final AmendmentRepository amendmentRepository;
    private final VectorizationService vectorizationService;
    private final HttpClient httpClient;

    public IngestionService(BillRepository billRepository,
                            SponsorRepository sponsorRepository,
                            ActionRepository actionRepository,
                            CommitteeRepository committeeRepository,
                            AmendmentRepository amendmentRepository,
                            VectorizationService vectorizationService) {
        this.billRepository = billRepository;
        this.sponsorRepository = sponsorRepository;
        this.actionRepository = actionRepository;
        this.committeeRepository = committeeRepository;
        this.amendmentRepository = amendmentRepository;
        this.vectorizationService = vectorizationService;
        this.httpClient = HttpClient.newHttpClient();
    }

    @Transactional
    public void saveBill(GovinfoBill govinfoBill) {
        if (govinfoBill == null || govinfoBill.billType == null || govinfoBill.billNumber == null) {
            logger.warn("Skipping bill with missing type or number.");
            return;
        }

        String baseBillId = govinfoBill.billType + govinfoBill.billNumber;
        DbBill dbBill = billRepository.findByBaseBillId(baseBillId).orElseGet(DbBill::new);

        dbBill.setBaseBillId(baseBillId);
        dbBill.setTitle(govinfoBill.title);
        dbBill.setFederalCongress(Integer.parseInt(govinfoBill.congress));
        dbBill.setFederalSource("govinfo.gov");
        dbBill.setSessionYear(CongressUtils.congressToSessionYear(Integer.parseInt(govinfoBill.congress)));

        if (govinfoBill.summaries != null && govinfoBill.summaries.billSummaries != null && !govinfoBill.summaries.billSummaries.isEmpty()) {
            govinfoBill.summaries.billSummaries.stream()
                .max(Comparator.comparing(s -> s.updateDate))
                .ifPresent(summary -> {
                    dbBill.setSummary(summary.text);
                    dbBill.setSummaryVector(vectorizationService.generateVector(summary.text));
                });
        }

        billRepository.saveAndFlush(dbBill);

        if (govinfoBill.actions != null) {
            for (GovinfoBill.Action action : govinfoBill.actions) {
                DbAction dbAction = new DbAction();
                dbAction.setBill(dbBill);
                dbAction.setActionDate(LocalDate.parse(action.actionDate, DateTimeFormatter.ISO_LOCAL_DATE));
                dbAction.setText(action.text);
                dbAction.setType(action.type);
                if (action.sourceSystem != null) {
                    dbAction.setChamber(action.sourceSystem.name);
                }
                actionRepository.save(dbAction);
            }
        }

        if (govinfoBill.sponsors != null) {
            for (GovinfoBill.Sponsor sponsor : govinfoBill.sponsors) {
                DbSponsor dbSponsor = sponsorRepository.findByMemberId(sponsor.bioguideId)
                    .orElseGet(() -> {
                        DbSponsor newSponsor = new DbSponsor();
                        newSponsor.setMemberId(sponsor.bioguideId);
                        newSponsor.setFullName(sponsor.fullName);
                        return sponsorRepository.save(newSponsor);
                    });
                if (dbBill.getSponsors().stream().noneMatch(s -> s.getId().equals(dbSponsor.getId()))) {
                    dbBill.getSponsors().add(dbSponsor);
                }
            }
        }

        billRepository.save(dbBill);

        if (govinfoBill.textVersions != null) {
            for (GovinfoBill.TextVersion textVersion : govinfoBill.textVersions) {
                textVersion.formats.stream()
                    .filter(format -> format.url.endsWith(".xml"))
                    .findFirst()
                    .ifPresent(format -> {
                        try {
                            String xmlContent = downloadText(format.url);
                            String plainText = extractTextFromXml(xmlContent);

                            DbAmendment amendment = new DbAmendment();
                            amendment.setBill(dbBill);
                            amendment.setVersion(textVersion.type);
                            amendment.setFullText(plainText);
                            amendment.setTextVector(vectorizationService.generateVector(plainText));
                            amendmentRepository.save(amendment);
                        } catch (IOException | InterruptedException e) {
                            logger.error("Failed to download or process text version from {}", format.url, e);
                        }
                    });
            }
        }
    }

    private String downloadText(String url) throws IOException, InterruptedException {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() == 200) {
            return response.body();
        } else {
            throw new IOException("Failed to download text from " + url + ". Status code: " + response.statusCode());
        }
    }

    private String extractTextFromXml(String xmlContent) {
        // This is a simplistic approach. A more robust implementation would use a proper XML parser.
        return xmlContent.replaceAll("<[^>]*>", " ").replaceAll("\\s+", " ").trim();
    }
}