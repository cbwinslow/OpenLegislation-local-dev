package gov.nysenate.openleg.processors.federal;

import gov.nysenate.openleg.dao.federal.FederalTranscriptDao;
import gov.nysenate.openleg.model.federal.FederalChamber;
import gov.nysenate.openleg.model.federal.FederalTranscript;
import org.junit.Before;
import org.junit.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.io.File;
import java.time.LocalDate;
import java.util.List;

import static org.junit.Assert.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

public class CongressionalRecordProcessorTest {

    @Mock
    private FederalTranscriptDao transcriptDao;

    private CongressionalRecordProcessor processor;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        processor = new CongressionalRecordProcessor();
        // Use reflection to set the DAO field
        try {
            java.lang.reflect.Field field = CongressionalRecordProcessor.class.getDeclaredField("transcriptDao");
            field.setAccessible(true);
            field.set(processor, transcriptDao);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    @Test
    void testProcessTranscriptFile_Success() throws Exception {
        // Create a mock XML file
        File testFile = createTestXmlFile();

        when(transcriptDao.save(any(FederalTranscript.class))).thenAnswer(invocation -> invocation.getArgument(0));

        List<FederalTranscript> result = processor.processTranscriptFile(testFile);

        assertNotNull(result);
        assertEquals(1, result.size());

        FederalTranscript transcript = result.get(0);
        assertEquals("CREC-2025-01-03", transcript.getTranscriptId());
        assertEquals(119, transcript.getCongress());
        assertEquals(LocalDate.of(2025, 1, 3), transcript.getDate());
        assertEquals("Test Transcript Title", transcript.getTitle());
        assertEquals(FederalChamber.SENATE, transcript.getChamber());

        // Clean up
        testFile.delete();
    }

    @Test
    void testProcessTranscriptFile_FileNotFound() {
        File nonExistentFile = new File("non_existent_file.xml");

        List<FederalTranscript> result = processor.processTranscriptFile(nonExistentFile);

        assertNotNull(result);
        assertEquals(0, result.size());
    }

    @Test
    void testProcessTranscriptFile_InvalidXml() throws Exception {
        File invalidXmlFile = createInvalidXmlFile();

        List<FederalTranscript> result = processor.processTranscriptFile(invalidXmlFile);

        assertNotNull(result);
        assertEquals(0, result.size());

        // Clean up
        invalidXmlFile.delete();
    }

    private File createTestXmlFile() throws Exception {
        String xmlContent = """
            <?xml version="1.0" encoding="UTF-8"?>
            <congressionalRecord>
                <congress>119</congress>
                <date>2025-01-03</date>
                <volume>172</volume>
                <title>Test Transcript Title</title>
                <chamber>Senate</chamber>
                <speech>
                    <speaker>Test Speaker</speaker>
                    <text>This is a test speech content.</text>
                </speech>
            </congressionalRecord>
            """;

        File testFile = File.createTempFile("test_transcript", ".xml");
        java.nio.file.Files.write(testFile.toPath(), xmlContent.getBytes());
        return testFile;
    }

    private File createInvalidXmlFile() throws Exception {
        String invalidXmlContent = "<invalid>xml<content>";

        File testFile = File.createTempFile("invalid_transcript", ".xml");
        java.nio.file.Files.write(testFile.toPath(), invalidXmlContent.getBytes());
        return testFile;
    }
}