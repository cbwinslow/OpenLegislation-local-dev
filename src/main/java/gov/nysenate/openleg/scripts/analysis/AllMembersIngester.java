package gov.nysenate.openleg.scripts.analysis;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.ComponentScan;
import gov.nysenate.openleg.service.federal.FederalIngestionService;
import gov.nysenate.openleg.model.federal.FederalMember;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.List;
import java.util.Map;

@ComponentScan
public class AllMembersIngester {

    private static final Logger logger = LoggerFactory.getLogger(AllMembersIngester.class);
    private final FederalIngestionService ingestionService;

    public AllMembersIngester(FederalIngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    public static void main(String[] args) {
        int startCong = 93, endCong = 119;
        for (String arg : args) {
            if (arg.startsWith("--start")) {
                startCong = Integer.parseInt(arg.substring("--start=".length()));
            } else if (arg.startsWith("--end")) {
                endCong = Integer.parseInt(arg.substring("--end=".length()));
            }
        }

        AnnotationConfigApplicationContext context = new AnnotationConfigApplicationContext(AppConfig.class);
        AllMembersIngester ingester = context.getBean(AllMembersIngester.class);
        ingester.ingestAllMembers(startCong, endCong);
        context.close();
    }

    private void ingestAllMembers(int start, int end) {
        Map<Integer, List<FederalMember>> allMembers = Maps.newHashMap();
        int total = 0, errors = 0;
        logger.info("Starting ingestion for congress {} to {}", start, end);

        for (int congress = start; congress <= end; congress++) {
            try {
                List<FederalMember> members = ingestionService.getMembers(congress);  // From API
                allMembers.put(congress, members);
                total += members.size();
                logger.info("Ingested {} members for congress {}", members.size(), congress);
            } catch (Exception e) {
                errors++;
                logger.error("Failed to ingest congress {}: {}", congress, e.getMessage());
            }
        }

        // Upsert all (dedup by bioguide_id)
        try {
            ingestionService.upsertAllMembers(allMembers.values());  // Batch upsert
            logger.info("Total ingested: {}, errors: {}", total - errors, errors);
        } catch (Exception e) {
            logger.error("Bulk upsert failed: {}", e.getMessage());
            errors++;
        }

        if (errors > 0) {
            logger.warn("Ingestion complete with {} errors; check logs for details", errors);
        } else {
            logger.info("Ingestion complete: {} unique members ingested (deduped by bioguide_id)", allMembers.size());
        }
    }
}
