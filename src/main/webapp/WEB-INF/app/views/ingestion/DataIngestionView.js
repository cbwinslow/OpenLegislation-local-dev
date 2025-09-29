import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from 'app/shared/Card';
import { Button } from 'app/shared/Button';
import { Input } from 'app/shared/Input';
import { Select } from 'app/shared/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from 'app/shared/Tabs';
import { Progress } from 'app/shared/Progress';
import { Alert, AlertDescription } from 'app/shared/Alert';
import { Badge } from 'app/shared/Badge';
import { Checkbox } from 'app/shared/Checkbox';
import { Textarea } from 'app/shared/Textarea';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from 'app/shared/Collapsible';
import { ChevronDown, ChevronRight, Database, Globe, Settings, Play, Pause, Square, Download, Upload, Calendar as CalendarIcon, Filter, BarChart3 } from 'lucide-react';

const DataIngestionView = () => {
  // Configuration state
  const [dataSources, setDataSources] = useState([
    { id: 'govinfo', name: 'GovInfo', type: 'api', enabled: true, description: 'Federal bills, laws, and documents' },
    { id: 'congress_gov', name: 'Congress.gov', type: 'website', enabled: true, description: 'Congressional information and legislation' },
    { id: 'house_gov', name: 'House.gov', type: 'website', enabled: false, description: 'House of Representatives data' },
    { id: 'senate_gov', name: 'Senate.gov', type: 'website', enabled: false, description: 'Senate data and information' },
    { id: 'federal_register', name: 'Federal Register', type: 'website', enabled: true, description: 'Federal rules and notices' },
    { id: 'whitehouse', name: 'WhiteHouse.gov', type: 'website', enabled: false, description: 'Executive branch information' },
    { id: 'state_databases', name: 'State Databases', type: 'database', enabled: false, description: 'State legislative data' }
  ]);

  const [selectedDataTypes, setSelectedDataTypes] = useState({
    bills: true,
    members: true,
    committees: false,
    votes: false,
    agendas: false,
    transcripts: false,
    laws: false,
    amendments: false,
    federal_bills: true,
    federal_members: true,
    federal_committees: false,
    federal_laws: false,
    social_media: false,
    press_releases: false
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

      // Set total operations for progress tracking
      const totalOperations = enabledTypes.length * enabledSources.length;
      setProgress(prev => ({
        ...prev,
        total: totalOperations
      }));

      // Simulate progress updates with federal data specifics
      let completedOps = 0;
      for (let i = 0; i < enabledTypes.length; i++) {
        const dataType = enabledTypes[i];

        for (let j = 0; j < enabledSources.length; j++) {
          const source = enabledSources[j];

          setProgress(prev => ({
            ...prev,
            currentDataType: dataType,
            currentOperation: `Processing ${dataType} from ${source.name}...`,
            completed: completedOps
          }));

          // Simulate processing time (longer for federal data)
          const processingTime = dataType.includes('federal') ? 3000 : 2000;
          await new Promise(resolve => setTimeout(resolve, processingTime));

          completedOps++;
          setProgress(prev => ({
            ...prev,
            completed: completedOps
          }));

          addLog(`${dataType} from ${source.name} processing completed`, 'success');

          // Add federal-specific log messages
          if (dataType.includes('federal')) {
            addLog(`Federal data validation completed for ${dataType}`, 'info');
          }
        }
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
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="sources">Data Sources</TabsTrigger>
          <TabsTrigger value="federal">Federal Members</TabsTrigger>
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

            {/* Federal Data Configuration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Globe className="w-5 h-5 mr-2" />
                  Federal Data Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="federalBills"
                      checked={selectedDataTypes.federal_bills}
                      onCheckedChange={(checked) =>
                        setSelectedDataTypes(prev => ({ ...prev, federal_bills: checked }))
                      }
                    />
                    <label htmlFor="federalBills" className="text-sm font-medium">
                      Federal Bills (BILLS Collection)
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="federalMembers"
                      checked={selectedDataTypes.federal_members}
                      onCheckedChange={(checked) =>
                        setSelectedDataTypes(prev => ({ ...prev, federal_members: checked }))
                      }
                    />
                    <label htmlFor="federalMembers" className="text-sm font-medium">
                      Federal Members (MEMBERS Collection)
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="federalCommittees"
                      checked={selectedDataTypes.federal_committees}
                      onCheckedChange={(checked) =>
                        setSelectedDataTypes(prev => ({ ...prev, federal_committees: checked }))
                      }
                    />
                    <label htmlFor="federalCommittees" className="text-sm font-medium">
                      Federal Committees (COMMITTEES Collection)
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="federalLaws"
                      checked={selectedDataTypes.federal_laws}
                      onCheckedChange={(checked) =>
                        setSelectedDataTypes(prev => ({ ...prev, federal_laws: checked }))
                      }
                    />
                    <label htmlFor="federalLaws" className="text-sm font-medium">
                      Federal Laws (LAWS Collection)
                    </label>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium mb-2">Federal-Specific Options</h4>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="includeSocialMedia"
                        checked={selectedDataTypes.social_media}
                        onCheckedChange={(checked) =>
                          setSelectedDataTypes(prev => ({ ...prev, social_media: checked }))
                        }
                      />
                      <label htmlFor="includeSocialMedia" className="text-sm">
                        Include social media data
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="includePressReleases"
                        checked={selectedDataTypes.press_releases}
                        onCheckedChange={(checked) =>
                          setSelectedDataTypes(prev => ({ ...prev, press_releases: checked }))
                        }
                      />
                      <label htmlFor="includePressReleases" className="text-sm">
                        Include press releases
                      </label>
                    </div>
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
                        <p className="text-xs text-gray-400">{source.description}</p>
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

        <TabsContent value="federal" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Federal Member Search */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Database className="w-5 h-5 mr-2" />
                  Federal Member Search
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Search by Name</label>
                    <Input placeholder="Enter member name..." />
                  </div>
                  <div>
                    <label className="text-sm font-medium">State</label>
                    <Select>
                      <option value="">All States</option>
                      <option value="AL">Alabama</option>
                      <option value="AK">Alaska</option>
                      <option value="AZ">Arizona</option>
                      <option value="AR">Arkansas</option>
                      <option value="CA">California</option>
                      <option value="CO">Colorado</option>
                      <option value="CT">Connecticut</option>
                      <option value="DE">Delaware</option>
                      <option value="FL">Florida</option>
                      <option value="GA">Georgia</option>
                      <option value="HI">Hawaii</option>
                      <option value="ID">Idaho</option>
                      <option value="IL">Illinois</option>
                      <option value="IN">Indiana</option>
                      <option value="IA">Iowa</option>
                      <option value="KS">Kansas</option>
                      <option value="KY">Kentucky</option>
                      <option value="LA">Louisiana</option>
                      <option value="ME">Maine</option>
                      <option value="MD">Maryland</option>
                      <option value="MA">Massachusetts</option>
                      <option value="MI">Michigan</option>
                      <option value="MN">Minnesota</option>
                      <option value="MS">Mississippi</option>
                      <option value="MO">Missouri</option>
                      <option value="MT">Montana</option>
                      <option value="NE">Nebraska</option>
                      <option value="NV">Nevada</option>
                      <option value="NH">New Hampshire</option>
                      <option value="NJ">New Jersey</option>
                      <option value="NM">New Mexico</option>
                      <option value="NY">New York</option>
                      <option value="NC">North Carolina</option>
                      <option value="ND">North Dakota</option>
                      <option value="OH">Ohio</option>
                      <option value="OK">Oklahoma</option>
                      <option value="OR">Oregon</option>
                      <option value="PA">Pennsylvania</option>
                      <option value="RI">Rhode Island</option>
                      <option value="SC">South Carolina</option>
                      <option value="SD">South Dakota</option>
                      <option value="TN">Tennessee</option>
                      <option value="TX">Texas</option>
                      <option value="UT">Utah</option>
                      <option value="VT">Vermont</option>
                      <option value="VA">Virginia</option>
                      <option value="WA">Washington</option>
                      <option value="WV">West Virginia</option>
                      <option value="WI">Wisconsin</option>
                      <option value="WY">Wyoming</option>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Party</label>
                    <Select>
                      <option value="">All Parties</option>
                      <option value="D">Democrat</option>
                      <option value="R">Republican</option>
                      <option value="I">Independent</option>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Chamber</label>
                    <Select>
                      <option value="">Both Chambers</option>
                      <option value="House">House</option>
                      <option value="Senate">Senate</option>
                    </Select>
                  </div>
                </div>
                <Button className="w-full">
                  Search Members
                </Button>
              </CardContent>
            </Card>

            {/* Member Data Quality */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Data Quality Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm">
                      <span>Total Federal Members</span>
                      <span className="font-medium">535</span>
                    </div>
                    <Progress value={100} className="mt-1" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm">
                      <span>With Complete Contact Info</span>
                      <span className="font-medium">98%</span>
                    </div>
                    <Progress value={98} className="mt-1" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm">
                      <span>With Social Media Links</span>
                      <span className="font-medium">87%</span>
                    </div>
                    <Progress value={87} className="mt-1" />
                  </div>
                  <div>
                    <div className="flex justify-between text-sm">
                      <span>Committee Assignments</span>
                      <span className="font-medium">92%</span>
                    </div>
                    <Progress value={92} className="mt-1" />
                  </div>
                </div>
                <div className="pt-4 border-t">
                  <h4 className="text-sm font-medium mb-2">Recent Updates</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Committee changes</span>
                      <Badge variant="outline">+12</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>New social media</span>
                      <Badge variant="outline">+8</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Contact updates</span>
                      <Badge variant="outline">+15</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Member Detail View Placeholder */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Federal Member Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8 text-gray-500">
                  <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Select a member from search results to view detailed information</p>
                  <p className="text-sm mt-2">Including terms, committees, social media, and contact information</p>
                </div>
              </CardContent>
            </Card>
          </div>
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