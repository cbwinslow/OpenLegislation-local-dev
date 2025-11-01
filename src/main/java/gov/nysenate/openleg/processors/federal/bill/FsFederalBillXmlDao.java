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

    private static final Pattern FEDERAL_XML_TYPE = Pattern.compile("(BILLS?|BILLSTATUS?|BILL-SUMMARIES?)-\\d+thCongress.*\\.XML", Pattern.CASE_INSENSITIVE);

    /**
     * Initialize filesystem directories for incoming and archived federal XML files.
     *
     * Sets {@code incomingSourceDir} to "{stagingDir}/federal-xmls" and
     * {@code archiveSourceDir} to "{archiveDir}/federal-xmls" using values from
     * the injected {@code environment}.
     */
    @PostConstruct
    protected void init() {
        incomingSourceDir = new File(environment.getStagingDir(), "federal-xmls");
        archiveSourceDir = new File(environment.getArchiveDir(), "federal-xmls");
    }

    /**
     * Gets the source type handled by this DAO.
     *
     * @return the source type `SourceType.FEDERAL_BILL_XML`
     */
    @Override
    public SourceType getSourceType() {
        return SourceType.FEDERAL_BILL_XML;
    }

    /**
     * Retrieve federal bill XML files from the incoming staging directory, filtered, ordered, and paginated.
     *
     * Applies the FEDERAL_XML_TYPE filename filter, orders by filename ascending (or descending when
     * {@code sortByFileName} is {@code SortOrder.DESC}), applies the provided {@code limitOffset}, and
     * returns the matching files wrapped as {@link FederalBillXmlFile} instances.
     *
     * @param sortByFileName controls ordering by filename; pass {@code SortOrder.DESC} for descending order
     * @param limitOffset    pagination limits and offset to apply to the result set; may be null to disable
     * @return a list of matching {@link FederalBillXmlFile} objects after filtering, ordering, and limiting
     * @throws IOException if the incoming source directory cannot be read
     */
    @Override
    public List<FederalBillXmlFile> getIncomingSourceFiles(SortOrder sortByFileName, LimitOffset limitOffset) throws IOException {
        List<File> files = new ArrayList<>(getSortedFiles(incomingSourceDir));
        files.removeIf(file -> !FEDERAL_XML_TYPE.matcher(file.getName()).matches());
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
     * Archives the given federal XML file by moving it from the incoming staging directory into the archive layout and marking it archived.
     *
     * @param federalFile the FederalBillXmlFile whose underlying file is in the incoming directory; its file reference and archived flag will be updated to the archive location
     * @throws IOException if the source file is not located in the incoming incoming directory or if an I/O error occurs while moving the file
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
     * Resolve a file path within the incoming federal XML staging directory by file name.
     *
     * @param fileName the name of the file in the incoming staging directory
     * @return the File representing the path to the named file in the incoming directory
     */
    @Override
    public File getFileInIncomingDir(String fileName) {
        return new File(incomingSourceDir, fileName);
    }

    /**
     * Resolve the archive file path for a federal bill XML using its published year and filename pattern.
     *
     * If the filename matches the FEDERAL_XML_TYPE pattern, the returned path is
     * {@code <archiveSourceDir>/<year>/<type>/<fileName>} where {@code year} is derived
     * from {@code publishedDateTime} and {@code type} is the lowercased regex group.
     * If the filename does not match the pattern, the returned path is
     * {@code <archiveSourceDir>/<fileName>}.
     *
     * @param fileName the name of the file to locate in the archive
     * @param publishedDateTime the publication date/time used to derive the archive year
     * @return a File pointing to the resolved archive location for the given filename
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
     * Wraps a filesystem File in a FederalBillXmlFile wrapper.
     *
     * @param file the XML file to wrap
     * @return a FederalBillXmlFile representing the provided file
     * @throws IOException if the file cannot be read or the wrapper fails to initialize
     */

    private FederalBillXmlFile toFederalXmlFile(File file) throws IOException {
        return new FederalBillXmlFile(file);
    }
}