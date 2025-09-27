package gov.nysenate.openleg.ingestion;

import com.google.gson.Gson;
import gov.nysenate.openleg.ingestion.model.GovinfoBill;
import gov.nysenate.openleg.service.IngestionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

@Component
public class GovinfoBulkIngester {

    private static final Logger logger = LoggerFactory.getLogger(GovinfoBulkIngester.class);
    private static final String BULK_DATA_URL_TEMPLATE = "https://www.govinfo.gov/bulkdata/json/BILLSTATUS/%d";

    private final HttpClient httpClient;
    private final IngestionService ingestionService;
    private final Gson gson;

    public GovinfoBulkIngester(IngestionService ingestionService) {
        this.httpClient = HttpClient.newHttpClient();
        this.ingestionService = ingestionService;
        this.gson = new Gson();
    }

    public void ingest(int congress) throws IOException, InterruptedException {
        String url = String.format(BULK_DATA_URL_TEMPLATE, congress);
        logger.info("Downloading bulk data from: {}", url);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .build();

        HttpResponse<byte[]> response = httpClient.send(request, HttpResponse.BodyHandlers.ofByteArray());
        if (response.statusCode() == 200) {
            logger.info("Download complete. Processing ZIP stream...");
            processZipStream(new ZipInputStream(new java.io.ByteArrayInputStream(response.body())));
        } else {
            logger.error("Failed to download bulk data. Status code: {}", response.statusCode());
        }
    }

    private void processZipStream(ZipInputStream zipInputStream) throws IOException {
        ZipEntry entry;
        while ((entry = zipInputStream.getNextEntry()) != null) {
            if (!entry.isDirectory() && entry.getName().endsWith(".json")) {
                logger.debug("Processing file: {}", entry.getName());

                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                byte[] buffer = new byte[1024];
                int len;
                while ((len = zipInputStream.read(buffer)) > 0) {
                    baos.write(buffer, 0, len);
                }
                String jsonContent = baos.toString(StandardCharsets.UTF_8);

                GovinfoBill govinfoBill = gson.fromJson(jsonContent, GovinfoBill.class);
                ingestionService.saveBill(govinfoBill);
            }
        }
        logger.info("Finished processing ZIP stream.");
    }
}