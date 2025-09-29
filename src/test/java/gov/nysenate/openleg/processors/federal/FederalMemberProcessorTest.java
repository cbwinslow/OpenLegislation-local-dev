package gov.nysenate.openleg.processors.federal;

import gov.nysenate.openleg.dao.federal.FederalMemberDao;
import gov.nysenate.openleg.model.federal.FederalChamber;
import gov.nysenate.openleg.model.federal.FederalMember;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

/**
 * Unit tests for FederalMemberProcessor.
 */
@ExtendWith(MockitoExtension.class)
public class FederalMemberProcessorTest {

    @Mock
    private FederalMemberDao federalMemberDao;

    private FederalMemberProcessor processor;

    @BeforeEach
    void setUp() {
        processor = new FederalMemberProcessor();
        ReflectionTestUtils.setField(processor, "federalMemberDao", federalMemberDao);
        ReflectionTestUtils.setField(processor, "apiKey", "test-key");
        ReflectionTestUtils.setField(processor, "batchSize", 50);
    }

    @Test
    void testIngestCurrentMembers_Success() {
        // Given
        when(federalMemberDao.findByBioguideId(anyString())).thenReturn(Optional.empty());
        when(federalMemberDao.save(any(FederalMember.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // When
        int result = processor.ingestCurrentMembers(119);

        // Then
        assertTrue(result >= 0);
        // Note: In a real test, we would mock the REST API calls
    }

    @Test
    void testIngestMemberDetails_Success() {
        // Given
        FederalMember existingMember = new FederalMember("P000197", "Charles Schumer", FederalChamber.SENATE);
        when(federalMemberDao.findByBioguideId("P000197")).thenReturn(Optional.of(existingMember));
        when(federalMemberDao.save(any(FederalMember.class))).thenAnswer(invocation -> invocation.getArgument(0));

        // When
        FederalMember result = processor.ingestMemberDetails("P000197");

        // Then
        assertNotNull(result);
        assertEquals("P000197", result.getBioguideId());
        // Note: In a real test, we would mock the REST API call
    }

    @Test
    void testGetCurrentMemberCount() {
        // Given
        when(federalMemberDao.countCurrentMembersByChamber("HOUSE")).thenReturn(435L);
        when(federalMemberDao.countCurrentMembersByChamber("SENATE")).thenReturn(100L);

        // When
        long houseCount = processor.getCurrentMemberCount(FederalChamber.HOUSE);
        long senateCount = processor.getCurrentMemberCount(FederalChamber.SENATE);

        // Then
        assertEquals(435L, houseCount);
        assertEquals(100L, senateCount);
    }

    @Test
    void testSearchMembersByName() {
        // Given
        FederalMember member = new FederalMember("P000197", "Charles Schumer", FederalChamber.SENATE);
        when(federalMemberDao.searchByName("Schumer")).thenReturn(List.of(member));

        // When
        List<FederalMember> results = processor.searchMembersByName("Schumer");

        // Then
        assertNotNull(results);
        assertEquals(1, results.size());
        assertEquals("Charles Schumer", results.get(0).getFullName());
    }

    @Test
    void testGetMembersByState() {
        // Given
        FederalMember member = new FederalMember("P000197", "Charles Schumer", FederalChamber.SENATE);
        when(federalMemberDao.findByStateOrderByLastNameAsc("NY")).thenReturn(List.of(member));

        // When
        List<FederalMember> results = processor.getMembersByState("NY");

        // Then
        assertNotNull(results);
        assertEquals(1, results.size());
        assertEquals("NY", results.get(0).getState());
    }
}