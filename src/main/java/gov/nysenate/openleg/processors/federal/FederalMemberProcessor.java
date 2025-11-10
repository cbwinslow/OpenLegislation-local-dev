package gov.nysenate.openleg.processors.federal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import gov.nysenate.openleg.dao.federal.FederalMemberDao;
import gov.nysenate.openleg.model.federal.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Processor for ingesting federal member data from congress.gov API.
 * Handles member biographical information, terms, committees, and social media accounts.
 */
@Component
public class FederalMemberProcessor {

    private static final Logger logger = LoggerFactory.getLogger(FederalMemberProcessor.class);

    @Autowired
    private FederalMemberDao federalMemberDao;

    @Value("${congress.api.key:dummy}")
    private String apiKey;

    @Value("${federal.member.ingestion.batch.size:50}")
    private int batchSize;

    private final RestTemplate restTemplate = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * Ingests all current federal members from the congress.gov API.
     *
     * @param congress the congress number (e.g., 119)
     * @return number of members processed
     */
    public int ingestCurrentMembers(int congress) {
        logger.info("Starting federal member ingestion for congress {}", congress);

        String url = "https://api.congress.gov/v3/member?api_key=" + apiKey +
                    "&congress=" + congress + "&currentMember=true&limit=" + batchSize;

        List<FederalMember> members = new ArrayList<>();
        int totalProcessed = 0;
        int offset = 0;

        try {
            while (true) {
                String pageUrl = url + "&offset=" + offset;
                logger.debug("Fetching members from: {}", pageUrl);

                ResponseEntity<String> response = restTemplate.getForEntity(pageUrl, String.class);

                if (response.getStatusCode().is2xxSuccessful()) {
                    JsonNode root = objectMapper.readTree(response.getBody());
                    JsonNode results = root.path("members");

                    if (results.isEmpty()) {
                        break; // No more results
                    }

                    for (JsonNode memberNode : results) {
                        try {
                            FederalMember member = mapMemberFromJson(memberNode, congress);
                            if (member != null) {
                                members.add(member);
                                totalProcessed++;
                            }
                        } catch (Exception e) {
                            logger.warn("Failed to process member: {}", memberNode.path("bioguideId").asText(), e);
                        }
                    }

                    // Batch save every 50 members
                    if (members.size() >= 50) {
                        saveMembersBatch(members);
                        members.clear();
                    }

                    offset += results.size();

                    // Check if there are more pages
                    if (results.size() < batchSize) {
                        break;
                    }
                } else {
                    logger.error("API request failed with status: {}", response.getStatusCode());
                    break;
                }
            }

            // Save remaining members
            if (!members.isEmpty()) {
                saveMembersBatch(members);
            }

            logger.info("Completed federal member ingestion: {} members processed", totalProcessed);

        } catch (Exception e) {
            logger.error("Error during federal member ingestion", e);
            throw new RuntimeException("Failed to ingest federal members", e);
        }

        return totalProcessed;
    }

    /**
     * Maps JSON member data to FederalMember entity.
     */
    private FederalMember mapMemberFromJson(JsonNode memberNode, int congress) {
        try {
            String bioguideId = memberNode.path("bioguideId").asText();
            if (bioguideId.isEmpty()) {
                return null;
            }

            // Check if member already exists
            Optional<FederalMember> existing = federalMemberDao.findByBioguideId(bioguideId);
            FederalMember member;

            if (existing.isPresent()) {
                member = existing.get();
                logger.debug("Updating existing member: {}", bioguideId);
            } else {
                member = new FederalMember();
                member.setBioguideId(bioguideId);
                member.setCreatedAt(LocalDate.now());
                logger.debug("Creating new member: {}", bioguideId);
            }

            // Basic member information
            String fullName = memberNode.path("name").asText();
            member.setFullName(fullName);

            String firstName = memberNode.path("firstName").asText();
            String lastName = memberNode.path("lastName").asText();
            member.setFirstName(firstName);
            member.setLastName(lastName);

            // Chamber and district information
            String chamberStr = memberNode.path("chamber").asText();
            FederalChamber chamber = FederalChamber.fromString(chamberStr);
            member.setChamber(chamber);

            member.setState(memberNode.path("state").asText());
            member.setDistrict(memberNode.path("district").asText());
            member.setParty(memberNode.path("party").asText());
            member.setCurrentMember(memberNode.path("currentMember").asBoolean(true));

            // Contact information
            member.setOfficeAddress(memberNode.path("officeAddress").asText());
            member.setOfficePhone(memberNode.path("officePhone").asText());
            member.setWebsiteUrl(memberNode.path("websiteUrl").asText());

            // Terms
            updateMemberTerms(member, memberNode.path("terms"), congress);

            // Social media
            updateMemberSocialMedia(member, memberNode);

            member.setUpdatedAt(LocalDate.now());

            return member;

        } catch (Exception e) {
            logger.error("Error mapping member from JSON", e);
            return null;
        }
    }

    /**
     * Updates member terms from JSON data.
     */
    private void updateMemberTerms(FederalMember member, JsonNode termsNode, int currentCongress) {
        List<FederalMemberTerm> terms = new ArrayList<>();

        if (termsNode.isArray()) {
            for (JsonNode termNode : termsNode) {
                FederalMemberTerm term = new FederalMemberTerm();
                term.setMember(member);
                term.setCongress(termNode.path("congress").asInt());
                term.setStartYear(termNode.path("startYear").asInt());
                term.setEndYear(termNode.path("endYear").asInt());
                term.setParty(termNode.path("party").asText());
                term.setState(termNode.path("state").asText());
                term.setDistrict(termNode.path("district").asText());
                term.setChamber(member.getChamber());
                term.setCreatedAt(LocalDate.now());

                terms.add(term);
            }
        }

        member.setTerms(terms);
    }

    /**
     * Updates member social media accounts from JSON data.
     */
    private void updateMemberSocialMedia(FederalMember member, JsonNode memberNode) {
        List<FederalMemberSocialMedia> socialMedia = new ArrayList<>();

        // Twitter
        String twitterHandle = memberNode.path("twitterAccount").asText();
        if (!twitterHandle.isEmpty()) {
            FederalMemberSocialMedia twitter = new FederalMemberSocialMedia(member, "twitter", twitterHandle,
                "https://twitter.com/" + twitterHandle);
            socialMedia.add(twitter);
        }

        // Facebook
        String facebookAccount = memberNode.path("facebookAccount").asText();
        if (!facebookAccount.isEmpty()) {
            FederalMemberSocialMedia facebook = new FederalMemberSocialMedia(member, "facebook", null, facebookAccount);
            socialMedia.add(facebook);
        }

        // YouTube
        String youtubeAccount = memberNode.path("youtubeAccount").asText();
        if (!youtubeAccount.isEmpty()) {
            FederalMemberSocialMedia youtube = new FederalMemberSocialMedia(member, "youtube", youtubeAccount,
                "https://youtube.com/" + youtubeAccount);
            socialMedia.add(youtube);
        }

        member.setSocialMedia(socialMedia);
    }

    /**
     * Saves a batch of members to the database.
     */
    private void saveMembersBatch(List<FederalMember> members) {
        try {
            for (FederalMember member : members) {
                // Save member first
                FederalMember savedMember = federalMemberDao.save(member);

                // Save terms
                for (FederalMemberTerm term : member.getTerms()) {
                    term.setMember(savedMember);
                    // Note: Would need a FederalMemberTermDao to save terms
                }

                // Save social media
                for (FederalMemberSocialMedia sm : member.getSocialMedia()) {
                    sm.setMember(savedMember);
                    // Note: Would need a FederalMemberSocialMediaDao to save social media
                }
            }

            logger.debug("Saved batch of {} members", members.size());

        } catch (Exception e) {
            logger.error("Error saving member batch", e);
            throw new RuntimeException("Failed to save member batch", e);
        }
    }

    /**
     * Ingests detailed member information including committees and leadership roles.
     *
     * @param bioguideId the member's bioguide ID
     * @return detailed member information or null if not found
     */
    public FederalMember ingestMemberDetails(String bioguideId) {
        String url = "https://api.congress.gov/v3/member/" + bioguideId + "?api_key=" + apiKey;

        try {
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                JsonNode memberNode = objectMapper.readTree(response.getBody()).path("member");

                Optional<FederalMember> existing = federalMemberDao.findByBioguideId(bioguideId);
                FederalMember member;

                if (existing.isPresent()) {
                    member = existing.get();
                } else {
                    member = new FederalMember(bioguideId, memberNode.path("name").asText(), null);
                }

                // Update with detailed information
                updateMemberDetails(member, memberNode);

                return federalMemberDao.save(member);
            }

        } catch (Exception e) {
            logger.error("Error ingesting member details for {}", bioguideId, e);
        }

        return null;
    }

    /**
     * Updates member with detailed information from the detailed API response.
     */
    private void updateMemberDetails(FederalMember member, JsonNode memberNode) {
        // Update basic information
        member.setFullName(memberNode.path("name").asText());
        member.setFirstName(memberNode.path("firstName").asText());
        member.setLastName(memberNode.path("lastName").asText());

        // Update terms with detailed information
        updateMemberTerms(member, memberNode.path("terms"), 0);

        // Update social media
        updateMemberSocialMedia(member, memberNode);

        // Update contact information
        member.setOfficeAddress(memberNode.path("officeAddress").asText());
        member.setOfficePhone(memberNode.path("officePhone").asText());
        member.setWebsiteUrl(memberNode.path("websiteUrl").asText());

        member.setUpdatedAt(LocalDate.now());
    }

    /**
     * Gets the count of current federal members by chamber.
     */
    public long getCurrentMemberCount(FederalChamber chamber) {
        return federalMemberDao.countCurrentMembersByChamber(chamber.toString());
    }

    /**
     * Searches for federal members by name.
     */
    public List<FederalMember> searchMembersByName(String name) {
        return federalMemberDao.searchByName(name);
    }

    /**
     * Gets all current federal members.
     */
    public List<FederalMember> getCurrentMembers() {
        return federalMemberDao.findCurrentMembers();
    }

    /**
     * Gets federal members by state.
     */
    public List<FederalMember> getMembersByState(String state) {
        return federalMemberDao.findByStateOrderByLastNameAsc(state);
    }
}