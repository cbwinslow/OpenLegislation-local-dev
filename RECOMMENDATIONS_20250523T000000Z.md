# Recommendations (2025-05-23)

- Add configuration files enumerating all ~30 endpoints per provider to avoid hard-coded lists and support schema-driven ingestion.
- Persist pagination checkpoints to disk or database so long-running pulls can resume after interruptions.
- Add unit tests that mock provider responses to verify pagination and rate limiting logic without live API calls.
- Integrate SQL normalization scripts from upstream repos to validate ingestion output against existing schemas.
