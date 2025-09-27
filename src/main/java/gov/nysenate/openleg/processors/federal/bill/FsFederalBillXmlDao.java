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

    @PostConstruct
    protected void init() {
        incomingSourceDir = new File(environment.getStagingDir(), "federal-xmls");
        archiveSourceDir = new File(environment.getArchiveDir(), "federal-xmls");
    }

    @Override
    public SourceType getSourceType() {
        return SourceType.FEDERAL_BILL_XML;
    }

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

    @Override
    public File getFileInIncomingDir(String fileName) {
        return new File(incomingSourceDir, fileName);
    }

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

    /* --- Internal Methods --- */

    private FederalBillXmlFile toFederalXmlFile(File file) throws IOException {
        return new FederalBillXmlFile(file);
    }
}
