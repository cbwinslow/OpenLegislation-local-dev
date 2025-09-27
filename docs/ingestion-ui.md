# Ingestion UI Documentation

## Setup
1. Add WebSocket config in Spring (WebSocketConfig.java with @EnableWebSocketMessageBroker, /ws endpoint).
2. Run Tomcat: mvn tomcat7:run.
3. Access: http://localhost:8080/ingest-ui.html.
4. Select site/collection, click Start—progress updates in real-time via WebSocket.

## Events
- /topic/progress: {ingested, total, successRate, status}.

## Extend
- Add more sites/collections in getRssUrl().
- React: Replace JS with React app for better UI.
