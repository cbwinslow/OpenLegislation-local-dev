package gov.nysenate.openleg.processors.bill.govinfo;

import gov.nysenate.openleg.processors.bill.BaseSourceFile;
import gov.nysenate.openleg.processors.bill.SourceType;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;

/**
 * Minimal GovInfoXmlFile placeholder — implement filename parsing as needed.
 */
public class GovInfoXmlFile extends BaseSourceFile {

    public GovInfoXmlFile(File file) throws IOException {
        super(file);
    }

    @Override
    public SourceType getSourceType() {
        return SourceType.XML;
    }

    @Override
    public LocalDateTime getPublishedDateTime() {
        // GovInfo filenames vary; implement parsing logic when mapping concrete files.
        return LocalDateTime.now();
    }
}
