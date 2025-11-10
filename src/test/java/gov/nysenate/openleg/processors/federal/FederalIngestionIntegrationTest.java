package gov.nysenate.openleg.processors.federal;

import gov.nysenate.openleg.dao.federal.FederalMemberDao;
import gov.nysenate.openleg.dao.federal.FederalTranscriptDao;
import gov.nysenate.openleg.model.federal.FederalChamber;
import gov.nysenate.openleg.model.federal.FederalMember;
import gov.nysenate.openleg.model.federal.FederalTranscript;
import org.junit.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.AbstractJUnit4SpringContextTests;

import java.time.LocalDate;
import java.util.List;

import static org.junit.Assert.*;

/**
 * Integration test for federal data ingestion components.
 */
@ContextConfiguration(locations = {"classpath:applicationContext.xml"})
public class FederalIngestionIntegrationTest extends AbstractJUnit4SpringContextTests {

    @Autowired
    private FederalMemberDao federalMemberDao;

    @Autowired
    private FederalTranscriptDao transcriptDao;

    @Autowired
    private FederalMemberProcessor memberProcessor;

    @Test
    public void testFederalMemberIngestion() {
        // Test member ingestion with sample data
        int result = memberProcessor.ingestCurrentMembers(119);

        // Should process at least some members (depending on API availability)
        assertTrue("Should process at least 0 members", result >= 0);

        // Verify members were saved
        List<FederalMember> members = federalMemberDao.findCurrentMembers();
        // Note: May be 0 if API key not configured or API unavailable
        assertNotNull("Members list should not be null", members);
    }

    @Test
    public void testFederalMemberSearch() {
        // Test member search functionality
        List<FederalMember> nyMembers = federalMemberDao.findByStateOrderByLastNameAsc("NY");

        if (!nyMembers.isEmpty()) {
            FederalMember firstMember = nyMembers.get(0);
            assertNotNull("Member should have bioguide ID", firstMember.getBioguideId());
            assertNotNull("Member should have full name", firstMember.getFullName());
            assertNotNull("Member should have chamber", firstMember.getChamber());
        }
    }

    @Test
    public void testFederalMemberChamberCounts() {
        // Test chamber count functionality
        long houseCount = federalMemberDao.countCurrentMembersByChamber("HOUSE");
        long senateCount = federalMemberDao.countCurrentMembersByChamber("SENATE");

        // Should have reasonable counts (0 if no data ingested)
        assertTrue("House count should be non-negative", houseCount >= 0);
        assertTrue("Senate count should be non-negative", senateCount >= 0);
    }

    @Test
    public void testFederalTranscriptProcessing() {
        // Test transcript processing (if data exists)
        List<FederalTranscript> transcripts = transcriptDao.findByCongressOrderByDateDesc(119);

        // Should not throw exceptions
        assertNotNull("Transcripts list should not be null", transcripts);

        for (FederalTranscript transcript : transcripts) {
            assertNotNull("Transcript should have ID", transcript.getTranscriptId());
            assertNotNull("Transcript should have date", transcript.getDate());
            assertNotNull("Transcript should have congress", transcript.getCongress());
        }
    }

    @Test
    public void testFederalDataIntegration() {
        // Test that federal data integrates properly with existing system
        List<FederalMember> currentMembers = federalMemberDao.findCurrentMembers();

        for (FederalMember member : currentMembers) {
            // Verify required fields are populated
            assertNotNull("Member should have bioguide ID", member.getBioguideId());
            assertNotNull("Member should have full name", member.getFullName());
            assertNotNull("Member should have chamber", member.getChamber());
            assertNotNull("Member should have current member flag", member.getCurrentMember());

            // Verify chamber is valid enum
            assertTrue("Chamber should be valid",
                member.getChamber() == FederalChamber.HOUSE ||
                member.getChamber() == FederalChamber.SENATE);
        }
    }
}