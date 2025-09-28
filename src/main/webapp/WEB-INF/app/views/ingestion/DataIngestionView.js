import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../shared/Card';
import { Button } from '../shared/Button';
import { Input } from '../shared/Input';
import { Select } from '../shared/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../shared/Tabs';
import { Progress } from '../shared/Progress';
import { Alert, AlertDescription } from '../shared/Alert';
import { Badge } from '../shared/Badge';
import { Calendar } from '../shared/Calendar';
import { Checkbox } from '../shared/Checkbox';
import { Textarea } from '../shared/Textarea';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../shared/Collapsible';
import { ChevronDown, ChevronRight, Database, Globe, Settings, Play, Pause, Square, Download, Upload, Calendar as CalendarIcon, Filter, BarChart3 } from 'lucide-react';

const DataIngestionView = () => {
  // Configuration state
  const [dataSources, setDataSources] = useState([
    { id: 'govinfo', name: 'GovInfo', type: 'api', enabled: true },
    { id: 'congress_gov', name: 'Congress.gov', type: 'website', enabled: true },
    { id: 'house_gov', name: 'House.gov', type: 'website', enabled: false },
    { id: 'senate_gov', name: 'Senate.gov', type: 'website', enabled: false },
    { id: 'federal_register', name: 'Federal Register', type: 'website', enabled: true },
    { id: 'whitehouse', name: 'WhiteHouse.gov', type: 'website', enabled: false },
    { id: 'state_databases', name: 'State Databases', type: 'database', enabled: false }
  ]);

  const [selectedDataTypes, setSelectedDataTypes] = useState({
    bills: true,
    members: true,
    committees: false,
    votes: false,
    agendas: false,
    transcripts: false,
    laws: false,
    amendments: false
  });

  const [dateRange, setDateRange] = useState({
    startDate: null,
    endDate: null
  });

  const [congressRange, setCongressRange] = useState({
    startCongress: 113,
    endCongress: 118
  });

  const [ingestionConfig, setIngestionConfig] = useState({
    batchSize: 100,
    maxRecords: 1000,
    parallelRequests: 5,
    retryAttempts: 3,
    timeout: 30000,
    validateData: true,
    createBackups: true,
    incrementalUpdate: false
  });

  const [deploymentConfig, setDeploymentConfig] = useState({
    createTables: false,
    updateSchema: false,
    backupBeforeDeploy: true,
    validateConstraints: true,
    targetDatabase: 'postgresql',
    connectionString: '',
    schemaName: 'master'
  });

  const [scheduleConfig, setScheduleConfig] = useState({
    enabled: false,
    frequency: 'daily',
    time: '02:00',
    daysOfWeek: [],
    daysOfMonth: [],
    enabledDataTypes: []
  });

  // Progress and status state
  const [isIngesting, setIsIngesting] = useState(false);
  const [progress, setProgress] = useState({
    total: 0,
    completed: 0,
    currentOperation: '',
    currentDataType: '',
    errors: [],
    warnings: [],
    startTime: null,
    estimatedCompletion: null
  });

  const [logs, setLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('configuration');
  const logsEndRef = useRef(null);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev, {
      timestamp: new Date().toISOString(),
      message,
      type
    }]);
  };

  const startIngestion = async () => {
    setIsIngesting(true);
    setProgress({
      total: 0,
      completed: 0,
      currentOperation: 'Initializing...',
      currentDataType: '',
      errors: [],
      warnings: [],
      startTime: new Date(),
      estimatedCompletion: null
    });
    setLogs([]);

    addLog('Starting data ingestion process...', 'info');

    try {
      // Simulate ingestion process
      const enabledSources = dataSources.filter(source => source.enabled);
      const enabledTypes = Object.entries(selectedDataTypes)
        .filter(([_, enabled]) => enabled)
        .map(([type, _]) => type);

      addLog(`Enabled data sources: ${enabledSources.map(s => s.name).join(', ')}`, 'info');
      addLog(`Enabled data types: ${enabledTypes.join(', ')}`, 'info');

      // Simulate progress updates
      for (let i = 0; i < enabledTypes.length; i++) {
        const dataType = enabledTypes[i];
        setProgress(prev => ({
          ...prev,
          currentDataType: dataType,
          currentOperation: `Processing ${dataType}...`
        }));

        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 2000));

        setProgress(prev => ({
          ...prev,
          completed: prev.completed + 1
        }));

        addLog(`${dataType} processing completed`, 'success');
      }

      addLog('Data ingestion completed successfully!', 'success');
    } catch (error) {
      addLog(`Error during ingestion: ${error.message}`, 'error');
      setProgress(prev => ({
        ...prev,
        errors: [...prev.errors, error.message]
      }));
    } finally {
      setIsIngesting(false);
    }
  };

  const stopIngestion = () => {
    setIsIngesting(false);
    addLog('Ingestion stopped by user', 'warning');
  };

  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Data Ingestion Center</h1>
          <p className="text-gray-600 mt-2">
            Configure and manage data ingestion from multiple sources into the legislative database
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={startIngestion}
            disabled={isIngesting}
            className="bg-green-600 hover:bg-green-700"
          >
            <Play className="w-4 h-4 mr-2" />
            {isIngesting ? 'Ingesting...' : 'Start Ingestion'}
          </Button>
          {isIngesting && (
            <Button
              onClick={stopIngestion}
              variant="destructive"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop
            </Button>
          )}
        </div>
      </div>

      {/* Progress Section */}
      {isIngesting && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Ingestion Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress
              value={(progress.completed / Math.max(progress.total, 1)) * 100}
              className="w-full"
            />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-medium">Current Operation:</span>
                <p className="text-blue-600">{progress.currentOperation}</p>
              </div>
              <div>
                <span className="font-medium">Data Type:</span>
                <p className="text-purple-600">{progress.currentDataType}</p>
              </div>
              <div>
                <span className="font-medium">Progress:</span>
                <p>{progress.completed}/{progress.total || '∞'}</p>
              </div>
              <div>
                <span className="font-medium">ETA:</span>
                <p>{progress.estimatedCompletion || 'Calculating...'}</p>
              </div>
            </div>
            {progress.errors.length > 0 && (
              <Alert variant="destructive">
                <AlertDescription>
                  {progress.errors.length} error(s) occurred during ingestion
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Main Configuration Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="sources">Data Sources</TabsTrigger>
          <TabsTrigger value="deployment">Deployment</TabsTrigger>
          <TabsTrigger value="scheduling">Scheduling</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
        </TabsList>

        <TabsContent value="configuration" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Data Type Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Filter className="w-5 h-5 mr-2" />
                  Data Types
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(selectedDataTypes).map(([type, enabled]) => (
                  <div key={type} className="flex items-center space-x-2">
                    <Checkbox
                      id={type}
                      checked={enabled}
                      onCheckedChange={(checked) =>
                        setSelectedDataTypes(prev => ({ ...prev, [type]: checked }))
                      }
                    />
                    <label htmlFor={type} className="text-sm font-medium capitalize">
                      {type}
                    </label>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Date Range Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <CalendarIcon className="w-5 h-5 mr-2" />
                  Date & Congress Range
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Start Congress</label>
                    <Input
                      type="number"
                      value={congressRange.startCongress}
                      onChange={(e) => setCongressRange(prev => ({
                        ...prev,
                        startCongress: parseInt(e.target.value)
                      }))}
                      min="1"
                      max="118"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">End Congress</label>
                    <Input
                      type="number"
                      value={congressRange.endCongress}
                      onChange={(e) => setCongressRange(prev => ({
                        ...prev,
                        endCongress: parseInt(e.target.value)
                      }))}
                      min="1"
                      max="118"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Start Date</label>
                    <Input
                      type="date"
                      value={dateRange.startDate || ''}
                      onChange={(e) => setDateRange(prev => ({
                        ...prev,
                        startDate: e.target.value
                      }))}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">End Date</label>
                    <Input
                      type="date"
                      value={dateRange.endDate || ''}
                      onChange={(e) => setDateRange(prev => ({
                        ...prev,
                        endDate: e.target.value
                      }))}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Ingestion Configuration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Settings className="w-5 h-5 mr-2" />
                  Ingestion Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Batch Size</label>
                    <Input
                      type="number"
                      value={ingestionConfig.batchSize}
                      onChange={(e) => setIngestionConfig(prev => ({
                        ...prev,
                        batchSize: parseInt(e.target.value)
                      }))}
                      min="1"
                      max="10000"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Max Records</label>
                    <Input
                      type="number"
                      value={ingestionConfig.maxRecords}
                      onChange={(e) => setIngestionConfig(prev => ({
                        ...prev,
                        maxRecords: parseInt(e.target.value)
                      }))}
                      min="1"
                      max="1000000"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Parallel Requests</label>
                    <Input
                      type="number"
                      value={ingestionConfig.parallelRequests}
                      onChange={(e) => setIngestionConfig(prev => ({
                        ...prev,
                        parallelRequests: parseInt(e.target.value)
                      }))}
                      min="1"
                      max="20"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Timeout (ms)</label>
                    <Input
                      type="number"
                      value={ingestionConfig.timeout}
                      onChange={(e) => setIngestionConfig(prev => ({
                        ...prev,
                        timeout: parseInt(e.target.value)
                      }))}
                      min="5000"
                      max="300000"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="validateData"
                      checked={ingestionConfig.validateData}
                      onCheckedChange={(checked) => setIngestionConfig(prev => ({
                        ...prev,
                        validateData: checked
                      }))}
                    />
                    <label htmlFor="validateData" className="text-sm">Validate data integrity</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="createBackups"
                      checked={ingestionConfig.createBackups}
                      onCheckedChange={(checked) => setIngestionConfig(prev => ({
                        ...prev,
                        createBackups: checked
                      }))}
                    />
                    <label htmlFor="createBackups" className="text-sm">Create backups before ingestion</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="incrementalUpdate"
                      checked={ingestionConfig.incrementalUpdate}
                      onCheckedChange={(checked) => setIngestionConfig(prev => ({
                        ...prev,
                        incrementalUpdate: checked
                      }))}
                    />
                    <label htmlFor="incrementalUpdate" className="text-sm">Incremental updates only</label>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full" variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  Export Configuration
                </Button>
                <Button className="w-full" variant="outline">
                  <Upload className="w-4 h-4 mr-2" />
                  Import Configuration
                </Button>
                <Button className="w-full" variant="outline">
                  Test Configuration
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="sources" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Globe className="w-5 h-5 mr-2" />
                Data Sources Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dataSources.map((source) => (
                  <div key={source.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${source.enabled ? 'bg-green-500' : 'bg-gray-300'}`} />
                      <div>
                        <h3 className="font-medium">{source.name}</h3>
                        <p className="text-sm text-gray-500 capitalize">{source.type}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={source.enabled ? 'default' : 'secondary'}>
                        {source.enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setDataSources(prev =>
                          prev.map(s => s.id === source.id ? { ...s, enabled: !s.enabled } : s)
                        )}
                      >
                        {source.enabled ? 'Disable' : 'Enable'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="deployment" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Database className="w-5 h-5 mr-2" />
                Database Deployment Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Target Database</label>
                  <Select
                    value={deploymentConfig.targetDatabase}
                    onValueChange={(value) => setDeploymentConfig(prev => ({
                      ...prev,
                      targetDatabase: value
                    }))}
                  >
                    <option value="postgresql">PostgreSQL</option>
                    <option value="mysql">MySQL</option>
                    <option value="sqlite">SQLite</option>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Schema Name</label>
                  <Input
                    value={deploymentConfig.schemaName}
                    onChange={(e) => setDeploymentConfig(prev => ({
                      ...prev,
                      schemaName: e.target.value
                    }))}
                    placeholder="master"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Connection String</label>
                <Textarea
                  value={deploymentConfig.connectionString}
                  onChange={(e) => setDeploymentConfig(prev => ({
                    ...prev,
                    connectionString: e.target.value
                  }))}
                  placeholder="postgresql://user:pass@localhost:5432/legislation"
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="createTables"
                    checked={deploymentConfig.createTables}
                    onCheckedChange={(checked) => setDeploymentConfig(prev => ({
                      ...prev,
                      createTables: checked
                    }))}
                  />
                  <label htmlFor="createTables" className="text-sm">Create tables if they don't exist</label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="updateSchema"
                    checked={deploymentConfig.updateSchema}
                    onCheckedChange={(checked) => setDeploymentConfig(prev => ({
                      ...prev,
                      updateSchema: checked
                    }))}
                  />
                  <label htmlFor="updateSchema" className="text-sm">Update schema if needed</label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="backupBeforeDeploy"
                    checked={deploymentConfig.backupBeforeDeploy}
                    onCheckedChange={(checked) => setDeploymentConfig(prev => ({
                      ...prev,
                      backupBeforeDeploy: checked
                    }))}
                  />
                  <label htmlFor="backupBeforeDeploy" className="text-sm">Create backup before deployment</label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="validateConstraints"
                    checked={deploymentConfig.validateConstraints}
                    onCheckedChange={(checked) => setDeploymentConfig(prev => ({
                      ...prev,
                      validateConstraints: checked
                    }))}
                  />
                  <label htmlFor="validateConstraints" className="text-sm">Validate constraints after deployment</label>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scheduling" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Automated Scheduling</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="scheduleEnabled"
                  checked={scheduleConfig.enabled}
                  onCheckedChange={(checked) => setScheduleConfig(prev => ({
                    ...prev,
                    enabled: checked
                  }))}
                />
                <label htmlFor="scheduleEnabled" className="text-sm font-medium">
                  Enable scheduled ingestion
                </label>
              </div>

              {scheduleConfig.enabled && (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium">Frequency</label>
                      <Select
                        value={scheduleConfig.frequency}
                        onValueChange={(value) => setScheduleConfig(prev => ({
                          ...prev,
                          frequency: value
                        }))}
                      >
                        <option value="hourly">Hourly</option>
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                      </Select>
                    </div>
                    <div>
                      <label className="text-sm font-medium">Time</label>
                      <Input
                        type="time"
                        value={scheduleConfig.time}
                        onChange={(e) => setScheduleConfig(prev => ({
                          ...prev,
                          time: e.target.value
                        }))}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium">Data Types to Include</label>
                    <div className="grid grid-cols-4 gap-2 mt-2">
                      {Object.keys(selectedDataTypes).map((type) => (
                        <div key={type} className="flex items-center space-x-2">
                          <Checkbox
                            id={`schedule-${type}`}
                            checked={scheduleConfig.enabledDataTypes.includes(type)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setScheduleConfig(prev => ({
                                  ...prev,
                                  enabledDataTypes: [...prev.enabledDataTypes, type]
                                }));
                              } else {
                                setScheduleConfig(prev => ({
                                  ...prev,
                                  enabledDataTypes: prev.enabledDataTypes.filter(t => t !== type)
                                }));
                              }
                            }}
                          />
                          <label htmlFor={`schedule-${type}`} className="text-sm capitalize">
                            {type}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="monitoring" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Ingestion Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center mb-4">
                <div className="flex space-x-2">
                  <Button size="sm" variant="outline" onClick={clearLogs}>
                    Clear Logs
                  </Button>
                  <Button size="sm" variant="outline">
                    Export Logs
                  </Button>
                </div>
                <div className="text-sm text-gray-500">
                  {logs.length} log entries
                </div>
              </div>
              <div className="bg-gray-50 border rounded-lg p-4 h-96 overflow-y-auto">
                <div className="space-y-2">
                  {logs.map((log, index) => (
                    <div key={index} className="flex items-start space-x-2 text-sm">
                      <span className="text-gray-500 font-mono">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <Badge
                        variant={
                          log.type === 'error' ? 'destructive' :
                          log.type === 'warning' ? 'secondary' :
                          log.type === 'success' ? 'default' : 'outline'
                        }
                        className="text-xs"
                      >
                        {log.type}
                      </Badge>
                      <span className="flex-1">{log.message}</span>
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DataIngestionView;