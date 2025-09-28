'use client'

import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/Select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/Tabs'
import { Progress } from './ui/Progress'
import { Alert, AlertDescription } from './ui/Alert'
import { Badge } from './ui/Badge'
import { Checkbox } from './ui/Checkbox'
import { Textarea } from './ui/Textarea'
import { Calendar } from './ui/Calendar'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/Dialog'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './ui/Collapsible'
import {
  Database,
  Globe,
  Settings,
  Play,
  Pause,
  Square,
  Download,
  Upload,
  Calendar as CalendarIcon,
  Filter,
  BarChart3,
  Bot,
  Brain,
  Vector,
  Table,
  FileText,
  Rocket,
  ChevronDown,
  ChevronRight,
  Search,
  Plus,
  Minus,
  Users,
  Clock,
  Target,
  Zap,
  Shield,
  GitBranch,
  MessageSquare,
  Code,
  Terminal,
  Server,
  Cloud,
  HardDrive,
  Cpu,
  Activity
} from 'lucide-react'

interface DataIngestionPlatformProps {
  className?: string
}

interface IngestionConfig {
  dataSources: DataSource[]
  selectedDataTypes: Record<string, boolean>
  dateRange: { startDate: string | null; endDate: string | null }
  congressRange: { startCongress: number; endCongress: number }
  memberFilters: MemberFilter[]
  batchSize: number
  maxRecords: number
  parallelRequests: number
  retryAttempts: number
  timeout: number
  validateData: boolean
  createBackups: boolean
  incrementalUpdate: boolean
  aiRagEnabled: boolean
  vectorizeData: boolean
  autoRag: boolean
}

interface DataSource {
  id: string
  name: string
  type: 'api' | 'website' | 'database'
  enabled: boolean
  url?: string
  credentials?: Record<string, string>
}

interface MemberFilter {
  id: string
  name: string
  state: string
  district: string
  party: string
  sessionYears: number[]
  enabled: boolean
}

interface ProgressState {
  total: number
  completed: number
  currentOperation: string
  currentDataType: string
  errors: string[]
  warnings: string[]
  startTime: Date | null
  estimatedCompletion: Date | null
  aiProcessing: boolean
  vectorization: boolean
}

export const DataIngestionPlatform: React.FC<DataIngestionPlatformProps> = ({
  className = ''
}) => {
  // Configuration state
  const [config, setConfig] = useState<IngestionConfig>({
    dataSources: [
      { id: 'govinfo', name: 'GovInfo', type: 'api', enabled: true, url: 'https://api.govinfo.gov' },
      { id: 'congress_gov', name: 'Congress.gov', type: 'website', enabled: true, url: 'https://congress.gov' },
      { id: 'house_gov', name: 'House.gov', type: 'website', enabled: false, url: 'https://house.gov' },
      { id: 'senate_gov', name: 'Senate.gov', type: 'website', enabled: false, url: 'https://senate.gov' },
      { id: 'federal_register', name: 'Federal Register', type: 'website', enabled: true, url: 'https://federalregister.gov' },
      { id: 'state_databases', name: 'State Databases', type: 'database', enabled: false }
    ],
    selectedDataTypes: {
      bills: true,
      members: true,
      committees: false,
      votes: false,
      agendas: false,
      transcripts: false,
      laws: false,
      amendments: false,
      social_media: false,
      news_feeds: false
    },
    dateRange: { startDate: null, endDate: null },
    congressRange: { startCongress: 113, endCongress: 118 },
    memberFilters: [],
    batchSize: 100,
    maxRecords: 1000,
    parallelRequests: 5,
    retryAttempts: 3,
    timeout: 30000,
    validateData: true,
    createBackups: true,
    incrementalUpdate: false,
    aiRagEnabled: true,
    vectorizeData: true,
    autoRag: false
  })

  // Progress and status state
  const [isIngesting, setIsIngesting] = useState(false)
  const [progress, setProgress] = useState<ProgressState>({
    total: 0,
    completed: 0,
    currentOperation: '',
    currentDataType: '',
    errors: [],
    warnings: [],
    startTime: null,
    estimatedCompletion: null,
    aiProcessing: false,
    vectorization: false
  })

  const [logs, setLogs] = useState<Array<{timestamp: string, message: string, type: string, source?: string}>>([])
  const [activeTab, setActiveTab] = useState('ingestion')
  const [showAiChat, setShowAiChat] = useState(false)
  const [showDatabaseViewer, setShowDatabaseViewer] = useState(false)
  const [showSqlWriter, setShowSqlWriter] = useState(false)
  const [showProgramLauncher, setShowProgramLauncher] = useState(false)
  const logsEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const addLog = (message: string, type: string = 'info', source?: string) => {
    setLogs(prev => [...prev, {
      timestamp: new Date().toISOString(),
      message,
      type,
      source
    }])
  }

  const startIngestion = async () => {
    setIsIngesting(true)
    setProgress({
      total: 0,
      completed: 0,
      currentOperation: 'Initializing AI-powered data ingestion...',
      currentDataType: '',
      errors: [],
      warnings: [],
      startTime: new Date(),
      estimatedCompletion: null,
      aiProcessing: config.aiRagEnabled,
      vectorization: config.vectorizeData
    })
    setLogs([])

    addLog('🚀 Starting AI-enhanced data ingestion process...', 'info', 'system')

    try {
      const enabledSources = config.dataSources.filter(source => source.enabled)
      const enabledTypes = Object.entries(config.selectedDataTypes)
        .filter(([_, enabled]) => enabled)
        .map(([type, _]) => type)

      addLog(`📡 Enabled data sources: ${enabledSources.map(s => s.name).join(', ')}`, 'info', 'config')
      addLog(`📋 Enabled data types: ${enabledTypes.join(', ')}`, 'info', 'config')
      addLog(`🤖 AI RAG: ${config.aiRagEnabled ? 'Enabled' : 'Disabled'}`, 'info', 'ai')
      addLog(`⚡ AutoRAG: ${config.autoRag ? 'Enabled' : 'Disabled'}`, 'info', 'ai')
      addLog(`🧠 Vectorization: ${config.vectorizeData ? 'Enabled' : 'Disabled'}`, 'info', 'ai')

      // Simulate AI-enhanced ingestion process
      for (let i = 0; i < enabledTypes.length; i++) {
        const dataType = enabledTypes[i]
        setProgress(prev => ({
          ...prev,
          currentDataType: dataType,
          currentOperation: `🤖 AI processing ${dataType} with RAG...`
        }))

        // AI RAG Processing
        if (config.aiRagEnabled) {
          await simulateAiRagProcessing(dataType)
        }

        // Vectorization
        if (config.vectorizeData) {
          await simulateVectorization(dataType)
        }

        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 2000))

        setProgress(prev => ({
          ...prev,
          completed: prev.completed + 1
        }))

        addLog(`✅ ${dataType} processing completed with AI enhancement`, 'success', 'ai')
      }

      addLog('🎉 AI-enhanced data ingestion completed successfully!', 'success', 'system')
    } catch (error) {
      addLog(`❌ Error during AI ingestion: ${error}`, 'error', 'system')
      setProgress(prev => ({
        ...prev,
        errors: [...prev.errors, String(error)]
      }))
    } finally {
      setIsIngesting(false)
    }
  }

  const simulateAiRagProcessing = async (dataType: string) => {
    addLog(`🧠 RAG: Analyzing ${dataType} patterns and relationships...`, 'info', 'ai')
    await new Promise(resolve => setTimeout(resolve, 1000))
    addLog(`🧠 RAG: Generating contextual embeddings for ${dataType}...`, 'info', 'ai')
    await new Promise(resolve => setTimeout(resolve, 800))
  }

  const simulateVectorization = async (dataType: string) => {
    addLog(`⚡ Vectorizing ${dataType} data for semantic search...`, 'info', 'ai')
    await new Promise(resolve => setTimeout(resolve, 1200))
  }

  const stopIngestion = () => {
    setIsIngesting(false)
    addLog('⏹️ AI ingestion stopped by user', 'warning', 'system')
  }

  const clearLogs = () => {
    setLogs([])
  }

  return (
    <div className={`container mx-auto p-6 space-y-6 ${className}`}>
      {/* Header with AI Features */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            🤖 AI-Powered Data Ingestion Platform
          </h1>
          <p className="text-gray-600 mt-2">
            Advanced legislative data platform with AI RAG, AutoRAG, vectorization, and intelligent processing
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            onClick={() => setShowAiChat(true)}
            className="bg-purple-600 hover:bg-purple-700"
          >
            <Bot className="w-4 h-4 mr-2" />
            AI Chat
          </Button>
          <Button
            onClick={() => setShowDatabaseViewer(true)}
            variant="outline"
          >
            <Table className="w-4 h-4 mr-2" />
            Database
          </Button>
          <Button
            onClick={() => setShowSqlWriter(true)}
            variant="outline"
          >
            <Code className="w-4 h-4 mr-2" />
            SQL Writer
          </Button>
          <Button
            onClick={() => setShowProgramLauncher(true)}
            variant="outline"
          >
            <Rocket className="w-4 h-4 mr-2" />
            Launch
          </Button>
          <Button
            onClick={startIngestion}
            disabled={isIngesting}
            className="bg-green-600 hover:bg-green-700"
          >
            <Play className="w-4 h-4 mr-2" />
            {isIngesting ? 'Processing...' : 'Start AI Ingestion'}
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

      {/* AI Progress Section */}
      {isIngesting && (
        <Card className="border-purple-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <CardHeader>
            <CardTitle className="flex items-center text-purple-700">
              <Brain className="w-5 h-5 mr-2" />
              AI-Enhanced Ingestion Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress
              value={(progress.completed / Math.max(progress.total, 1)) * 100}
              className="w-full h-3"
            />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-medium text-purple-600">Current Operation:</span>
                <p className="text-blue-600">{progress.currentOperation}</p>
              </div>
              <div>
                <span className="font-medium text-purple-600">Data Type:</span>
                <p className="text-purple-600">{progress.currentDataType}</p>
              </div>
              <div>
                <span className="font-medium text-purple-600">AI Processing:</span>
                <p className={progress.aiProcessing ? 'text-green-600' : 'text-gray-500'}>
                  {progress.aiProcessing ? '🧠 Active' : '⏸️ Inactive'}
                </p>
              </div>
              <div>
                <span className="font-medium text-purple-600">Vectorization:</span>
                <p className={progress.vectorization ? 'text-green-600' : 'text-gray-500'}>
                  {progress.vectorization ? '⚡ Active' : '⏸️ Inactive'}
                </p>
              </div>
            </div>
            {progress.errors.length > 0 && (
              <Alert variant="destructive">
                <AlertDescription>
                  {progress.errors.length} error(s) occurred during AI processing
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Main Interface Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="ingestion">🚀 Ingestion</TabsTrigger>
          <TabsTrigger value="ai-rag">🧠 AI RAG</TabsTrigger>
          <TabsTrigger value="vectorizer">⚡ Vectorizer</TabsTrigger>
          <TabsTrigger value="database">🗄️ Database</TabsTrigger>
          <TabsTrigger value="deployment">☁️ Deploy</TabsTrigger>
          <TabsTrigger value="programs">🚀 Programs</TabsTrigger>
        </TabsList>

        <TabsContent value="ingestion" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Enhanced Data Type Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Filter className="w-5 h-5 mr-2" />
                  Enhanced Data Types & AI Processing
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(config.selectedDataTypes).map(([type, enabled]) => (
                  <div key={type} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id={type}
                        checked={enabled}
                        onCheckedChange={(checked) =>
                          setConfig(prev => ({
                            ...prev,
                            selectedDataTypes: { ...prev.selectedDataTypes, [type]: checked }
                          }))
                        }
                      />
                      <label htmlFor={type} className="text-sm font-medium capitalize">
                        {type.replace('_', ' ')}
                      </label>
                    </div>
                    <div className="flex space-x-2">
                      {enabled && config.aiRagEnabled && (
                        <Badge variant="secondary" className="text-xs">
                          <Brain className="w-3 h-3 mr-1" />
                          RAG
                        </Badge>
                      )}
                      {enabled && config.vectorizeData && (
                        <Badge variant="secondary" className="text-xs">
                          <Vector className="w-3 h-3 mr-1" />
                          Vector
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Fine-Grained Member Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  Member & Time Period Selection
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Start Congress</label>
                    <Input
                      type="number"
                      value={config.congressRange.startCongress}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        congressRange: { ...prev.congressRange, startCongress: parseInt(e.target.value) }
                      }))}
                      min="1"
                      max="118"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">End Congress</label>
                    <Input
                      type="number"
                      value={config.congressRange.endCongress}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        congressRange: { ...prev.congressRange, endCongress: parseInt(e.target.value) }
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
                      value={config.dateRange.startDate || ''}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        dateRange: { ...prev.dateRange, startDate: e.target.value }
                      }))}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">End Date</label>
                    <Input
                      type="date"
                      value={config.dateRange.endDate || ''}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        dateRange: { ...prev.dateRange, endDate: e.target.value }
                      }))}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Member Filters</label>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {config.memberFilters.map((member) => (
                      <div key={member.id} className="flex items-center space-x-2 p-2 border rounded">
                        <Checkbox
                          checked={member.enabled}
                          onCheckedChange={(checked) => {
                            setConfig(prev => ({
                              ...prev,
                              memberFilters: prev.memberFilters.map(m =>
                                m.id === member.id ? { ...m, enabled: checked } : m
                              )
                            }))
                          }}
                        />
                        <span className="text-sm">{member.name} ({member.state}-{member.district})</span>
                      </div>
                    ))}
                    <Button size="sm" variant="outline" className="w-full">
                      <Plus className="w-4 h-4 mr-2" />
                      Add Member Filter
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AI-Enhanced Configuration */}
            <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center text-purple-700">
                  <Brain className="w-5 h-5 mr-2" />
                  AI Processing Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="aiRagEnabled"
                      checked={config.aiRagEnabled}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        aiRagEnabled: checked
                      }))}
                    />
                    <label htmlFor="aiRagEnabled" className="text-sm font-medium">
                      Enable AI RAG Processing
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="vectorizeData"
                      checked={config.vectorizeData}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        vectorizeData: checked
                      }))}
                    />
                    <label htmlFor="vectorizeData" className="text-sm font-medium">
                      Enable Data Vectorization
                    </label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="autoRag"
                      checked={config.autoRag}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        autoRag: checked
                      }))}
                    />
                    <label htmlFor="autoRag" className="text-sm font-medium">
                      Enable AutoRAG (Automatic RAG Generation)
                    </label>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">AI Model</label>
                    <Select defaultValue="gpt-4">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gpt-4">GPT-4</SelectItem>
                        <SelectItem value="claude-3">Claude 3</SelectItem>
                        <SelectItem value="local-llm">Local LLM</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Vector Dimensions</label>
                    <Select defaultValue="1536">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="768">768 (Small)</SelectItem>
                        <SelectItem value="1536">1536 (Medium)</SelectItem>
                        <SelectItem value="3072">3072 (Large)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Performance & Quality Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Zap className="w-5 h-5 mr-2" />
                  Performance & Quality Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium">Batch Size</label>
                    <Input
                      type="number"
                      value={config.batchSize}
                      onChange={(e) => setConfig(prev => ({
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
                      value={config.maxRecords}
                      onChange={(e) => setConfig(prev => ({
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
                      value={config.parallelRequests}
                      onChange={(e) => setConfig(prev => ({
                        ...prev,
                        parallelRequests: parseInt(e.target.value)
                      }))}
                      min="1"
                      max="20"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">AI Timeout (ms)</label>
                    <Input
                      type="number"
                      value={config.timeout}
                      onChange={(e) => setConfig(prev => ({
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
                      checked={config.validateData}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        validateData: checked
                      }))}
                    />
                    <label htmlFor="validateData" className="text-sm">AI-powered data validation</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="createBackups"
                      checked={config.createBackups}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        createBackups: checked
                      }))}
                    />
                    <label htmlFor="createBackups" className="text-sm">Create AI-processed backups</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="incrementalUpdate"
                      checked={config.incrementalUpdate}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        incrementalUpdate: checked
                      }))}
                    />
                    <label htmlFor="incrementalUpdate" className="text-sm">Incremental AI updates only</label>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="ai-rag" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* AI RAG Chat Interface */}
            <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50">
              <CardHeader>
                <CardTitle className="flex items-center text-purple-700">
                  <MessageSquare className="w-5 h-5 mr-2" />
                  AI RAG Assistant
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="h-64 bg-white border rounded-lg p-4 overflow-y-auto">
                    <div className="space-y-3">
                      <div className="flex items-start space-x-2">
                        <Bot className="w-5 h-5 text-purple-600 mt-1" />
                        <div className="bg-purple-100 p-3 rounded-lg max-w-xs">
                          <p className="text-sm">Hello! I'm your AI RAG assistant. I can help you analyze legislative data, generate insights, and answer questions about bills, members, and government processes.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Input placeholder="Ask me about legislative data..." className="flex-1" />
                    <Button className="bg-purple-600 hover:bg-purple-700">
                      <MessageSquare className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AutoRAG Configuration */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <GitBranch className="w-5 h-5 mr-2" />
                  AutoRAG Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">AutoRAG Status</span>
                    <Badge variant={config.autoRag ? 'default' : 'secondary'}>
                      {config.autoRag ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">RAG Generation</span>
                    <Button size="sm" variant="outline">
                      Generate RAG
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Vector Updates</span>
                    <Button size="sm" variant="outline">
                      Update Vectors
                    </Button>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">RAG Template</label>
                  <Textarea
                    placeholder="Enter custom RAG template..."
                    rows={4}
                    className="mt-1"
                  />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="vectorizer" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Vector className="w-5 h-5 mr-2" />
                Data Vectorization Center
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 border rounded-lg">
                    <Vector className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                    <h3 className="font-medium">Text Vectorization</h3>
                    <p className="text-sm text-gray-600">Convert text to embeddings</p>
                    <Button size="sm" className="mt-2 w-full">Vectorize</Button>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <BarChart3 className="w-8 h-8 mx-auto mb-2 text-green-600" />
                    <h3 className="font-medium">Semantic Search</h3>
                    <p className="text-sm text-gray-600">Search with meaning</p>
                    <Button size="sm" className="mt-2 w-full">Search</Button>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <Target className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                    <h3 className="font-medium">Similarity Analysis</h3>
                    <p className="text-sm text-gray-600">Find similar content</p>
                    <Button size="sm" className="mt-2 w-full">Analyze</Button>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium">Vectorization Progress</label>
                  <Progress value={75} className="mt-2" />
                  <p className="text-xs text-gray-600 mt-1">Processing bills and amendments...</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="database" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Database Viewer */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Table className="w-5 h-5 mr-2" />
                  Database Tables
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {['bill', 'member', 'committee', 'vote', 'agenda'].map((table) => (
                    <div key={table} className="flex items-center justify-between p-2 border rounded">
                      <span className="font-medium capitalize">{table}</span>
                      <div className="flex space-x-2">
                        <Button size="sm" variant="outline">View</Button>
                        <Button size="sm" variant="outline">Query</Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* SQL Query Interface */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Code className="w-5 h-5 mr-2" />
                  SQL Query Builder
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Query</label>
                    <Textarea
                      placeholder="SELECT * FROM bill WHERE session_year = 118 LIMIT 100;"
                      rows={6}
                      className="font-mono text-sm"
                    />
                  </div>
                  <div className="flex space-x-2">
                    <Button size="sm">Execute</Button>
                    <Button size="sm" variant="outline">Format</Button>
                    <Button size="sm" variant="outline">Save</Button>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Results</label>
                    <div className="h-32 bg-gray-100 border rounded p-2 overflow-auto">
                      <p className="text-sm text-gray-600">Query results will appear here...</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="deployment" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Deployment Options */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Cloud className="w-5 h-5 mr-2" />
                  Deployment Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Deployment Target</label>
                  <Select defaultValue="vercel">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="vercel">Vercel</SelectItem>
                      <SelectItem value="netlify">Netlify</SelectItem>
                      <SelectItem value="cloudflare">Cloudflare Pages</SelectItem>
                      <SelectItem value="aws">AWS Amplify</SelectItem>
                      <SelectItem value="gcp">Google Cloud</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Environment</label>
                  <Select defaultValue="production">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="development">Development</SelectItem>
                      <SelectItem value="staging">Staging</SelectItem>
                      <SelectItem value="production">Production</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox id="autoDeploy" defaultChecked />
                    <label htmlFor="autoDeploy" className="text-sm">Auto-deploy on changes</label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox id="backupBeforeDeploy" defaultChecked />
                    <label htmlFor="backupBeforeDeploy" className="text-sm">Backup before deployment</label>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Program Launcher */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Terminal className="w-5 h-5 mr-2" />
                  Program Launcher
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    <Button size="sm" variant="outline">
                      <Server className="w-4 h-4 mr-2" />
                      Start Backend
                    </Button>
                    <Button size="sm" variant="outline">
                      <Database className="w-4 h-4 mr-2" />
                      Start Database
                    </Button>
                    <Button size="sm" variant="outline">
                      <Vector className="w-4 h-4 mr-2" />
                      Start Vector DB
                    </Button>
                    <Button size="sm" variant="outline">
                      <Bot className="w-4 h-4 mr-2" />
                      Start AI Service
                    </Button>
                  </div>
                  <div>
                    <label className="text-sm font-medium">Custom Command</label>
                    <Input placeholder="npm run dev" className="mt-1" />
                    <Button size="sm" className="mt-2 w-full">Execute</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="programs" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Cpu className="w-5 h-5 mr-2" />
                Running Programs & Services
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { name: 'Next.js Frontend', status: 'running', port: 3000, cpu: 15, memory: 128 },
                  { name: 'Java Backend', status: 'running', port: 8080, cpu: 25, memory: 256 },
                  { name: 'PostgreSQL Database', status: 'running', port: 5432, cpu: 10, memory: 64 },
                  { name: 'Redis Cache', status: 'stopped', port: 6379, cpu: 0, memory: 0 },
                  { name: 'AI RAG Service', status: 'running', port: 8001, cpu: 35, memory: 512 },
                  { name: 'Vector Database', status: 'running', port: 8000, cpu: 20, memory: 256 }
                ].map((service) => (
                  <div key={service.name} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${service.status === 'running' ? 'bg-green-500' : 'bg-red-500'}`} />
                      <div>
                        <h3 className="font-medium">{service.name}</h3>
                        <p className="text-sm text-gray-600">Port {service.port}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-sm">CPU: {service.cpu}%</p>
                        <p className="text-sm">RAM: {service.memory}MB</p>
                      </div>
                      <Button size="sm" variant={service.status === 'running' ? 'destructive' : 'default'}>
                        {service.status === 'running' ? 'Stop' : 'Start'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Enhanced Logs Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              AI Processing Logs
            </span>
            <div className="flex space-x-2">
              <Button size="sm" variant="outline" onClick={clearLogs}>
                Clear Logs
              </Button>
              <Button size="sm" variant="outline">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 border rounded-lg p-4 h-96 overflow-y-auto">
            <div className="space-y-2">
              {logs.map((log, index) => (
                <div key={index} className="flex items-start space-x-2 text-sm">
                  <span className="text-gray-500 font-mono text-xs">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <Badge
                    variant={
                      log.type === 'error' ? 'destructive' :
                      log.type === 'warning' ? 'secondary' :
                      log.type === 'success' ? 'default' :
                      log.type === 'ai' ? 'outline' : 'outline'
                    }
                    className="text-xs"
                  >
                    {log.source || log.type}
                  </Badge>
                  <span className="flex-1">{log.message}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI Chat Dialog */}
      <Dialog open={showAiChat} onOpenChange={setShowAiChat}>
        <DialogContent className="max-w-4xl h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center text-purple-700">
              <Bot className="w-5 h-5 mr-2" />
              AI RAG Assistant
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 flex flex-col">
            <div className="flex-1 bg-gray-50 rounded-lg p-4 mb-4 overflow-y-auto">
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <Bot className="w-6 h-6 text-purple-600 mt-1" />
                  <div className="bg-white p-3 rounded-lg shadow-sm max-w-md">
                    <p className="text-sm">Hello! I'm your AI assistant specialized in legislative data analysis. I can help you with:</p>
                    <ul className="text-xs mt-2 space-y-1">
                      <li>• Analyzing bill patterns and trends</li>
                      <li>• Finding similar legislation</li>
                      <li>• Member voting pattern analysis</li>
                      <li>• Committee activity insights</li>
                      <li>• Legislative process guidance</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex space-x-2">
              <Input placeholder="Ask me anything about legislative data..." className="flex-1" />
              <Button className="bg-purple-600 hover:bg-purple-700">
                <MessageSquare className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Database Viewer Dialog */}
      <Dialog open={showDatabaseViewer} onOpenChange={setShowDatabaseViewer}>
        <DialogContent className="max-w-6xl h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Table className="w-5 h-5 mr-2" />
              Database Viewer & Query Interface
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 grid grid-cols-3 gap-4">
            <div className="col-span-1 space-y-4">
              <h3 className="font-medium">Tables</h3>
              <div className="space-y-2">
                {['bill', 'member', 'committee', 'vote', 'agenda', 'transcript'].map((table) => (
                  <Button key={table} variant="outline" className="w-full justify-start">
                    <Table className="w-4 h-4 mr-2" />
                    {table}
                  </Button>
                ))}
              </div>
            </div>
            <div className="col-span-2 space-y-4">
              <div>
                <h3 className="font-medium mb-2">SQL Query</h3>
                <Textarea
                  placeholder="SELECT * FROM bill WHERE session_year = 118 ORDER BY created_date_time DESC LIMIT 100;"
                  rows={8}
                  className="font-mono text-sm"
                />
              </div>
              <div className="flex space-x-2">
                <Button>Execute Query</Button>
                <Button variant="outline">Format SQL</Button>
                <Button variant="outline">Save Query</Button>
              </div>
              <div>
                <h3 className="font-medium mb-2">Results</h3>
                <div className="h-64 bg-gray-100 border rounded p-2 overflow-auto">
                  <p className="text-sm text-gray-600">Query results will appear here...</p>
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* SQL Writer Dialog */}
      <Dialog open={showSqlWriter} onOpenChange={setShowSqlWriter}>
        <DialogContent className="max-w-4xl h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Code className="w-5 h-5 mr-2" />
              AI-Powered SQL Script Writer
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 grid grid-cols-2 gap-4">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Natural Language Query</label>
                <Textarea
                  placeholder="I need to find all bills sponsored by members from California in the 118th Congress that relate to healthcare..."
                  rows={6}
                  className="mt-1"
                />
              </div>
              <Button className="w-full bg-purple-600 hover:bg-purple-700">
                <Bot className="w-4 h-4 mr-2" />
                Generate SQL
              </Button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Generated SQL</label>
                <Textarea
                  value="SELECT b.*, m.full_name as sponsor_name, m.state FROM bill b JOIN bill_sponsor bs ON b.bill_print_no = bs.bill_print_no AND b.bill_session_year = bs.bill_session_year JOIN session_member sm ON bs.session_member_id = sm.id JOIN member m ON sm.member_id = m.id WHERE m.state = 'CA' AND b.bill_session_year = 118 AND b.title ILIKE '%health%' ORDER BY b.created_date_time DESC;"
                  rows={8}
                  className="font-mono text-sm mt-1"
                  readOnly
                />
              </div>
              <div className="flex space-x-2">
                <Button>Execute</Button>
                <Button variant="outline">Copy</Button>
                <Button variant="outline">Optimize</Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Program Launcher Dialog */}
      <Dialog open={showProgramLauncher} onOpenChange={setShowProgramLauncher}>
        <DialogContent className="max-w-4xl h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Rocket className="w-5 h-5 mr-2" />
              Program & Service Launcher
            </DialogTitle>
          </DialogHeader>
          <div className="flex-1 grid grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-medium">Quick Launch</h3>
              <div className="grid grid-cols-2 gap-2">
                <Button className="h-20 flex-col">
                  <Server className="w-6 h-6 mb-2" />
                  Backend API
                </Button>
                <Button variant="outline" className="h-20 flex-col">
                  <Database className="w-6 h-6 mb-2" />
                  Database
                </Button>
                <Button variant="outline" className="h-20 flex-col">
                  <Vector className="w-6 h-6 mb-2" />
                  Vector DB
                </Button>
                <Button className="h-20 flex-col bg-purple-600 hover:bg-purple-700">
                  <Bot className="w-6 h-6 mb-2" />
                  AI Service
                </Button>
              </div>
              <div>
                <label className="text-sm font-medium">Custom Command</label>
                <Input placeholder="docker-compose up -d" className="mt-1" />
                <Button className="mt-2 w-full">Execute Command</Button>
              </div>
            </div>
            <div className="space-y-4">
              <h3 className="font-medium">Service Status</h3>
              <div className="space-y-2">
                {[
                  { name: 'Next.js Frontend', status: 'running', url: 'http://localhost:3000' },
                  { name: 'Java Backend', status: 'running', url: 'http://localhost:8080' },
                  { name: 'PostgreSQL', status: 'running', url: 'localhost:5432' },
                  { name: 'Redis Cache', status: 'stopped', url: 'localhost:6379' },
                  { name: 'AI RAG Service', status: 'running', url: 'http://localhost:8001' },
                  { name: 'Vector Database', status: 'running', url: 'http://localhost:8000' }
                ].map((service) => (
                  <div key={service.name} className="flex items-center justify-between p-2 border rounded">
                    <div>
                      <p className="font-medium text-sm">{service.name}</p>
                      <p className="text-xs text-gray-600">{service.url}</p>
                    </div>
                    <Badge variant={service.status === 'running' ? 'default' : 'secondary'}>
                      {service.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}