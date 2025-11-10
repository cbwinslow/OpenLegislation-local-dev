
### 22:23 UTC - INFO: 🚀 Starting GPU-accelerated parallel ingestion - Sources: ['congress_api', 'govinfo_bulk', 'openstates', 'openlegislature'], Workers: 8, GPU: True
### 22:23 UTC - INFO: 🔍 Checking prerequisites...
### 22:23 UTC - INFO: ✅ Redis connection: PASSED
### 22:23 UTC - INFO: ✅ Database connection: PASSED
### 22:23 UTC - INFO: ✅ GPU availability: PASSED
### 22:23 UTC - INFO: ✅ Scripts existence: PASSED
### 22:23 UTC - INFO: ✅ Disk space: PASSED
### 22:23 UTC - INFO: ✅ API keys: PASSED
### 22:23 UTC - INFO: Enqueued 18 jobs for congress_api
### 22:23 UTC - INFO: Enqueued 12 jobs for govinfo_bulk
### 22:23 UTC - INFO: Enqueued 10 jobs for openstates
### 22:23 UTC - INFO: Enqueued 3 jobs for openlegislature
### 22:23 UTC - INFO: Total enqueued: 43 jobs across 4 sources
### 22:23 UTC - INFO: Started 8 async workers with GPU acceleration: True
### 22:23 UTC - INFO: Waiting for ingestion completion (timeout: 2h)
### 22:23 UTC - INFO: Progress update: Queue: 35 pending, 0 processed | Recent: 0/0 success | Overall: 0.0% success rate | GPU: 0.0% avg utilization
### 22:24 UTC - INFO: All ingestion jobs completed successfully
### 22:24 UTC - INFO: Progress update: Queue: 0 pending, 43 processed | Recent: 0/20 success | Overall: 0.0% success rate | GPU: 0.0% avg utilization
### 22:24 UTC - INFO: Final report generated: 0/43 jobs successful (0.0%)
### 22:24 UTC - WARNING: ⚠️ Ingestion completed with low success rate: 0.0%