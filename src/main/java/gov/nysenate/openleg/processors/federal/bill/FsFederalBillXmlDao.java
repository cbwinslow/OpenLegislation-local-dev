package gov.nysenate.openleg.processors.federal.bill;

import gov.nysenate.openleg.common.dao.LimitOffset;
import gov.nysenate.openleg.common.dao.SortOrder;
import gov.nysenate.openleg.common.util.FileIOUtils;
import gov.nysenate.openleg.config.OpenLegEnvironment;
import gov.nysenate.openleg.processors.bill.SourceType;
import gov.nysenate.openleg.processors.sourcefile.SourceFileFsDao;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;

import javax.annotation.PostConstruct;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static gov.nysenate.openleg.common.util.FileIOUtils.getSortedFiles;

/**
 * DAO for federal bill XML files from staging directory.
 * Customized for congress.gov/govinfo XML.
 */
@Repository
public class FsFederalBillXmlDao implements SourceFileFsDao<FederalBillXmlFile> {

    private static final Logger logger = LoggerFactory.getLogger(FsFederalBillXmlDao.class);

    @Autowired
    protected OpenLegEnvironment environment;

    private File incomingSourceDir;
    private File archiveSourceDir;


    /**
     * Initialize filesystem locations for incoming and archived federal XML files.
     *
     * Sets {@code incomingSourceDir} to "<stagingDir>/federal-xmls" and {@code archiveSourceDir}
     * to "<archiveDir>/federal-xmls" using the injected environment. Executed after bean construction.
     */
    @PostConstruct
    protected void init() {
        incomingSourceDir = new File(environment.getStagingDir(), "federal-xmls");
        archiveSourceDir = new File(environment.getArchiveDir(), "federal-xmls");
    }

    /**
     * Identify the source type handled by this DAO.
     *
     * @return `SourceType.FEDERAL_BILL_XML` indicating the DAO manages federal bill XML source files.
     */
    @Override
    public SourceType getSourceType() {
        return SourceType.FEDERAL_BILL_XML;
    }

    /**
     * Retrieve incoming federal bill XML files from the staging directory, filtered by filename pattern,
     * ordered by filename according to the provided sort order, and restricted by the provided pagination.
     *
     * @param sortByFileName controls the filename sort order; use {@code SortOrder.DESC} to reverse the order
     * @param limitOffset    pagination limits and offset to apply to the result set
     * @return               a list of {@link FederalBillXmlFile} instances for files whose names match
     *                       {@code FederalBillXmlFile.FILENAME_PATTERN}, ordered and paginated as requested
     */
    @Override
    public List<FederalBillXmlFile> getIncomingSourceFiles(SortOrder sortByFileName, LimitOffset limitOffset) throws IOException {
        List<File> files = new ArrayList<>(getSortedFiles(incomingSourceDir));
        files.removeIf(file -> !FederalBillXmlFile.FILENAME_PATTERN.matcher(file.getName()).matches());
        if (sortByFileName == SortOrder.DESC) {
            Collections.reverse(files);
        }
        files = LimitOffset.limitList(files, limitOffset);
        List<FederalBillXmlFile> federalFiles = new ArrayList<>();
        for (File file : files) {
            federalFiles.add(toFederalXmlFile(file));
        }
        return federalFiles;
    }

    /**
     * Moves the specified federal bill XML file from the incoming directory to the archive directory,
     * updating its file reference and archive status.
     *
     * @param federalFile the federal bill XML file to archive
     * @throws IOException if an I/O error occurs during the file move or if the file is not located in the incoming directory
     */
    @Override
    public void archiveSourceFile(FederalBillXmlFile federalFile) throws IOException {
        File stageFile = federalFile.getFile();
        if (stageFile.getParentFile().equals(incomingSourceDir)) {
            File archiveFile = getFileInArchiveDir(federalFile.getFileName(), federalFile.getPublishedDateTime());
            FileIOUtils.moveFile(stageFile, archiveFile);
            federalFile.setFile(archiveFile);
            federalFile.setArchived(true);
        } else {
            throw new FileNotFoundException("FederalBillXmlFile " + stageFile + " must be in the incoming federal-xmls directory.");
        }
    }

    /**
     * Returns the file with the specified name located in the incoming source directory.
     *
     * @param fileName the name of the file
     * @return the file located in the incoming source directory with the given name
     */
    @Override
    public File getFileInIncomingDir(String fileName) {
        return new File(incomingSourceDir, fileName);
    }

    /**
     * Determine the expected archived file location for a federal bill XML using its file name and publication year.
     *
     * @param fileName the XML file's name
     * @param publishedDateTime the file's published date/time used to derive the archive year
     * @return a File pointing to the archive path; if the file name matches the FEDERAL_XML_TYPE pattern the path is
     *         "<archiveRoot>/<year>/<type>/<fileName>", otherwise "<archiveRoot>/<fileName>"
     */
    @Override
    public File getFileInArchiveDir(String fileName, LocalDateTime publishedDateTime) {
        String year = Integer.toString(publishedDateTime.getYear());
        Matcher matcher = FEDERAL_XML_TYPE.matcher(fileName);
        if (matcher.find()) {
            String type = matcher.group(1).toLowerCase();
            File dir = new File(archiveSourceDir + "/" + year, type);
            return new File(dir, fileName);
        }
        return new File(archiveSourceDir, fileName);
    }

    /**
     * Wraps the given filesystem File into a FederalBillXmlFile.
     *
     * @param file the XML file on disk
     * @return a FederalBillXmlFile representing the provided file
     * @throws IOException if the file cannot be read or initialized
     */

    private FederalBillXmlFile toFederalXmlFile(File file) throws IOException {
        return new FederalBillXmlFile(file);
    }
}