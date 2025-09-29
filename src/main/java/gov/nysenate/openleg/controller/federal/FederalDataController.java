package gov.nysenate.openleg.controller.federal;

import gov.nysenate.openleg.dao.federal.FederalMemberDao;
import gov.nysenate.openleg.model.federal.*;
import gov.nysenate.openleg.processors.federal.FederalMemberProcessor;
import gov.nysenate.openleg.service.federal.FederalIngestionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * REST API controller for federal legislative data.
 * Provides endpoints for accessing federal bills, members, committees, and other data.
 */
@RestController
@RequestMapping("/api/3/federal")
public class FederalDataController {

    private static final Logger logger = LoggerFactory.getLogger(FederalDataController.class);

    @Autowired
    private FederalMemberDao federalMemberDao;

    @Autowired
    private FederalMemberProcessor federalMemberProcessor;

    @Autowired
    private FederalIngestionService federalIngestionService;

    /**
     * Get all current federal members.
     */
    @GetMapping("/members")
    public ResponseEntity<List<FederalMember>> getFederalMembers(
            @RequestParam(required = false) String chamber,
            @RequestParam(required = false) String state,
            @RequestParam(required = false) String party) {

        try {
            List<FederalMember> members;

            if (chamber != null) {
                members = federalMemberDao.findByChamberOrderByStateAscDistrictAsc(chamber.toUpperCase());
            } else if (state != null) {
                members = federalMemberDao.findByStateOrderByLastNameAsc(state.toUpperCase());
            } else if (party != null) {
                members = federalMemberDao.findByPartyOrderByStateAscLastNameAsc(party.toUpperCase());
            } else {
                members = federalMemberDao.findCurrentMembers();
            }

            return ResponseEntity.ok(members);

        } catch (Exception e) {
            logger.error("Error fetching federal members", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * Get a specific federal member by bioguide ID.
     */
    @GetMapping("/members/{bioguideId}")
    public ResponseEntity<FederalMember> getFederalMember(@PathVariable String bioguideId) {
        try {
            return federalMemberDao.findByBioguideId(bioguideId)
                    .map(ResponseEntity::ok)
                    .orElse(ResponseEntity.notFound().build());

        } catch (Exception e) {
            logger.error("Error fetching federal member: {}", bioguideId, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * Search federal members by name.
     */
    @GetMapping("/members/search")
    public ResponseEntity<List<FederalMember>> searchFederalMembers(@RequestParam String name) {
        try {
            List<FederalMember> members = federalMemberProcessor.searchMembersByName(name);
            return ResponseEntity.ok(members);

        } catch (Exception e) {
            logger.error("Error searching federal members: {}", name, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * Get federal members by state.
     */
    @GetMapping("/members/state/{state}")
    public ResponseEntity<List<FederalMember>> getFederalMembersByState(@PathVariable String state) {
        try {
            List<FederalMember> members = federalMemberProcessor.getMembersByState(state.toUpperCase());
            return ResponseEntity.ok(members);

        } catch (Exception e) {
            logger.error("Error fetching federal members by state: {}", state, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * Get federal member statistics.
     */
    @GetMapping("/members/stats")
    public ResponseEntity<FederalMemberStats> getFederalMemberStats() {
        try {
            long houseCount = federalMemberProcessor.getCurrentMemberCount(FederalChamber.HOUSE);
            long senateCount = federalMemberProcessor.getCurrentMemberCount(FederalChamber.SENATE);

            FederalMemberStats stats = new FederalMemberStats(houseCount, senateCount);
            return ResponseEntity.ok(stats);

        } catch (Exception e) {
            logger.error("Error fetching federal member stats", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * Trigger federal data ingestion.
     */
    @PostMapping("/ingest")
    public ResponseEntity<FederalIngestionResponse> triggerFederalIngestion(
            @RequestParam int congress,
            @RequestParam(required = false, defaultValue = "false") boolean includeMembers) {

        try {
            logger.info("Triggering federal ingestion for congress {}", congress);

            CompletableFuture<FederalIngestionService.FederalIngestionResult> billsFuture =
                federalIngestionService.ingestFederalData(congress);

            CompletableFuture<FederalIngestionService.FederalMemberIngestionResult> membersFuture = null;
            if (includeMembers) {
                membersFuture = federalIngestionService.ingestFederalMembers(congress);
            }

            FederalIngestionResponse response = new FederalIngestionResponse(
                congress, "STARTED", "Federal ingestion started for congress " + congress);

            return ResponseEntity.ok(response);

        } catch (Exception e) {
            logger.error("Error triggering federal ingestion", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * Get federal ingestion status.
     */
    @GetMapping("/ingest/status/{congress}")
    public ResponseEntity<FederalIngestionService.FederalIngestionStatus> getIngestionStatus(
            @PathVariable int congress) {

        try {
            FederalIngestionService.FederalIngestionStatus status =
                federalIngestionService.getIngestionStatus(congress);
            return ResponseEntity.ok(status);

        } catch (Exception e) {
            logger.error("Error fetching ingestion status for congress {}", congress, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    /**
     * Validate federal data integrity.
     */
    @PostMapping("/validate/{congress}")
    public ResponseEntity<FederalIngestionService.FederalDataValidationResult> validateFederalData(
            @PathVariable int congress) {

        try {
            FederalIngestionService.FederalDataValidationResult result =
                federalIngestionService.validateFederalData(congress);
            return ResponseEntity.ok(result);

        } catch (Exception e) {
            logger.error("Error validating federal data for congress {}", congress, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    // Response DTOs

    public static class FederalMemberStats {
        private final long houseMembers;
        private final long senateMembers;
        private final long totalMembers;

        public FederalMemberStats(long houseMembers, long senateMembers) {
            this.houseMembers = houseMembers;
            this.senateMembers = senateMembers;
            this.totalMembers = houseMembers + senateMembers;
        }

        public long getHouseMembers() { return houseMembers; }
        public long getSenateMembers() { return senateMembers; }
        public long getTotalMembers() { return totalMembers; }
    }

    public static class FederalIngestionResponse {
        private final int congress;
        private final String status;
        private final String message;

        public FederalIngestionResponse(int congress, String status, String message) {
            this.congress = congress;
            this.status = status;
            this.message = message;
        }

        public int getCongress() { return congress; }
        public String getStatus() { return status; }
        public String getMessage() { return message; }
    }
}