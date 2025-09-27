package gov.nysenate.openleg.ingestion;

import com.google.gson.Gson;
import gov.nysenate.openleg.ingestion.model.GovinfoBill;
import gov.nysenate.openleg.service.IngestionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

@Component
public class GovinfoApiIngester {

    private static final Logger logger = LoggerFactory.getLogger(GovinfoApiIngester.class);
    private static final String API_URL_TEMPLATE = "https://api.govinfo.gov/packages/%s/summary";

    private final HttpClient httpClient;
    private final String apiKey;
    private final IngestionService ingestionService;
    private final Gson gson;

    public GovinfoApiIngester(IngestionService ingestionService) {
        this.httpClient = HttpClient.newHttpClient();
        this.ingestionService = ingestionService;
        this.apiKey = System.getenv("GOVINFO_API_KEY");
        if (this.apiKey == null || this.apiKey.isEmpty()) {
            throw new IllegalStateException("GOVINFO_API_KEY environment variable not set.");
        }
        this.gson = new Gson();
    }

    public void ingest(String packageId) throws IOException, InterruptedException {
        String url = String.format(API_URL_TEMPLATE, packageId);
        logger.info("Fetching data from API: {}", url);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("X-Api-Key", apiKey)
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() == 200) {
            logger.info("Successfully fetched data for package: {}", packageId);
            processJsonResponse(response.body());
        } else {
            logger.error("Failed to fetch data from API for package {}. Status code: {}", packageId, response.statusCode());
        }
    }

    private void processJsonResponse(String jsonResponse) {
        GovinfoBill govinfoBill = gson.fromJson(jsonResponse, GovinfoBill.class);
        ingestionService.saveBill(govinfoBill);
    }
}