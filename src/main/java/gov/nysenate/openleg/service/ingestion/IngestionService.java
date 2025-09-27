package gov.nysenate.openleg.service.ingestion;

import com.rometools.rome.feed.synd.SyndEntry;
import com.rometools.rome.feed.synd.SyndFeed;
import com.rometools.rome.io.SyndFeedInput;
import com.rometools.rome.io.XmlReader;
import gov.nysenate.openleg.dao.document.DocumentRepository;
import gov.nysenate.openleg.model.document.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.io.InputStream;
import java.net.URL;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Transactional
public class IngestionService {

    private static final Logger logger = LoggerFactory.getLogger(IngestionService.class);

    @Autowired
    private DocumentRepository documentRepository;

    private final RestTemplate restTemplate = new RestTemplate();

    /**
     * Ingest documents from RSS feed.
     * @param rssUrl RSS feed URL
     * @param source Source name for documents
     */
    public void ingestFromRSS(String rssUrl, String source) {
        try (InputStream inputStream = new URL(rssUrl).openStream()) {
            SyndFeed feed = new SyndFeedInput().build(new XmlReader(inputStream));
            List<SyndEntry> entries = feed.getEntries();

            logger.info("Ingesting {} entries from {} ({})", entries.size(), rssUrl, source);

            List<Document> documents = entries.stream()
                    .filter(entry -> !documentRepository.existsByUrl(entry.getLink()))
                    .map(entry -> {
                        Document doc = new Document();
                        doc.setSource(source);
                        doc.setUrl(entry.getLink());
                        doc.setTitle(entry.getTitle());
                        doc.setDescription(entry.getDescription().getValue());
                        if (entry.getPublishedDate() != null) {
                            doc.setPubDate(LocalDateTime.ofInstant(entry.getPublishedDate().toInstant(), ZoneOffset.UTC));
                        }
                        // For content, use description or fetch full if needed
                        doc.setContent(entry.getDescription().getValue());
                        // Metadata as JSON string
                        Map<String, Object> metadata = Map.of(
                                "author", entry.getAuthor(),
                                "categories", entry.getCategories().stream().map(c -> c.getName()).collect(Collectors.toList())
                        );
                        doc.setMetadata(gson.toJson(metadata));  // Assume Gson injected or static
                        return doc;
                    })
                    .collect(Collectors.toList());

            documentRepository.saveAll(documents);
            logger.info("Saved {} new documents from {}", documents.size(), source);
        } catch (Exception e) {
            logger.error("Error ingesting from RSS {}: {}", rssUrl, e.getMessage());
        }
    }

    /**
     * Scheduled ingestion for WikiLeaks.
     */
    @Scheduled(fixedRate = 1800000)  // Every 30 min
    public void ingestWikiLeaks() {
        ingestFromRSS("https://wikileaks.org/feed.xml", "wikileaks");
    }

    /**
     * Scheduled ingestion for CDC.
     */
    @Scheduled(fixedRate = 3600000)  // Every hour
    public void ingestCDC() {
        ingestFromRSS("https://tools.cdc.gov/api/v2/resources/rss", "cdc");
    }

    /**
     * Scheduled ingestion for WhiteHouse (President).
     */
    @Scheduled(fixedRate = 3600000)
    public void ingestWhiteHouse() {
        ingestFromRSS("https://www.whitehouse.gov/briefing-room/speeches-remarks/feed/", "whitehouse");
    }

    /**
     * Scheduled ingestion for Reuters news.
     */
    @Scheduled(fixedRate = 3600000)
    public void ingestReuters() {
        ingestFromRSS("https://feeds.reuters.com/reuters/topNews", "reuters");
    }

    /**
     * Example for data.gov API (legislation datasets; requires API key if rate-limited).
     */
    public void ingestFromDataGov(String resourceId, String source) {
        String url = "https://catalog.data.gov/api/3/action/datastore_search?resource_id=" + resourceId + "&limit=100";
        ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
        if (response.getBody() != null) {
            List<Map> records = (List<Map>) ((Map) response.getBody().get("result")).get("records");
            records.stream()
                    .filter(record -> !documentRepository.existsByUrl((String) record.get("url")))  // Assume url field
                    .map(record -> {
                        Document doc = new Document();
                        doc.setSource(source);
                        doc.setUrl((String) record.get("url"));
                        doc.setTitle((String) record.get("title"));
                        doc.setDescription((String) record.get("description"));
                        doc.setContent((String) record.get("content"));
                        doc.setMetadata(gson.toJson(record));  // Full record as metadata
                        return doc;
                    })
                    .forEach(documentRepository::save);
        }
    }

    // Note: Inject Gson if needed
    // @Autowired private Gson gson;
}
