import "core-js/stable";
import "regenerator-runtime/runtime";

/**
 * Start data ingestion process with the specified configuration
 * @param {Object} config - Ingestion configuration
 * @param {Array} config.dataSources - Enabled data sources
 * @param {Object} config.dataTypes - Selected data types
 * @param {Object} config.dateRange - Date range for ingestion
 * @param {Object} config.congressRange - Congress range for ingestion
 * @param {Object} config.ingestionConfig - Ingestion settings
 * @param {Object} config.deploymentConfig - Deployment configuration
 * @returns {Promise}
 */
export async function startIngestion(config) {
  const response = await fetch('/api/ingestion/start', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config)
  });

  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data;
}

/**
 * Stop the current ingestion process
 * @returns {Promise}
 */
export async function stopIngestion() {
  const response = await fetch('/api/ingestion/stop', {
    method: 'POST'
  });

  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data;
}

/**
 * Get current ingestion progress
 * @returns {Promise}
 */
export async function getIngestionProgress() {
  const response = await fetch('/api/ingestion/progress');
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data.result;
}

/**
 * Get ingestion logs
 * @param {number} limit - Maximum number of logs to retrieve
 * @param {string} level - Log level filter (info, warning, error)
 * @returns {Promise}
 */
export async function getIngestionLogs(limit = 100, level = null) {
  let url = `/api/ingestion/logs?limit=${limit}`;
  if (level) {
    url += `&level=${level}`;
  }

  const response = await fetch(url);
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data.result;
}

/**
 * Test ingestion configuration
 * @param {Object} config - Configuration to test
 * @returns {Promise}
 */
export async function testIngestionConfig(config) {
  const response = await fetch('/api/ingestion/test', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config)
  });

  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data;
}

/**
 * Get available data sources
 * @returns {Promise}
 */
export async function getDataSources() {
  const response = await fetch('/api/ingestion/data-sources');
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data.result;
}

/**
 * Get available data types for ingestion
 * @returns {Promise}
 */
export async function getDataTypes() {
  const response = await fetch('/api/ingestion/data-types');
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data.result;
}

/**
 * Deploy database schema
 * @param {Object} config - Deployment configuration
 * @returns {Promise}
 */
export async function deploySchema(config) {
  const response = await fetch('/api/ingestion/deploy', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config)
  });

  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data;
}

/**
 * Schedule automated ingestion
 * @param {Object} scheduleConfig - Scheduling configuration
 * @returns {Promise}
 */
export async function scheduleIngestion(scheduleConfig) {
  const response = await fetch('/api/ingestion/schedule', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(scheduleConfig)
  });

  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data;
}

/**
 * Get scheduled ingestion jobs
 * @returns {Promise}
 */
export async function getScheduledJobs() {
  const response = await fetch('/api/ingestion/schedule');
  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data.result;
}

/**
 * Export ingestion configuration
 * @param {Object} config - Configuration to export
 * @returns {Promise}
 */
export async function exportConfiguration(config) {
  const response = await fetch('/api/ingestion/export', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config)
  });

  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data;
}

/**
 * Import ingestion configuration
 * @param {string} configFile - Configuration file content
 * @returns {Promise}
 */
export async function importConfiguration(configFile) {
  const formData = new FormData();
  formData.append('config', configFile);

  const response = await fetch('/api/ingestion/import', {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  if (!data.success) {
    throw new Error(data.message);
  }
  return data;
}