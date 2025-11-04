import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const {
      source,
      endpoint,
      congressNumber,
      state,
      startDate,
      endDate,
      batchSize,
      maxRecords,
      dryRun
    } = body

    // Build command line arguments for the Python script
    const projectRoot = path.resolve(process.cwd(), '..')
    const scriptPath = path.join(projectRoot, 'tools', 'ingest_congress_api.py')
    
    const args = [
      scriptPath,
      '--source', source || 'congress',
      '--endpoint', endpoint || 'bill',
      '--batch', String(batchSize || 50)
    ]

    if (dryRun) {
      args.push('--dry-run')
    }

    if (maxRecords) {
      args.push('--max-records', String(maxRecords))
    }

    // Add source-specific arguments
    if (source === 'congress' && congressNumber) {
      args.push('congress', '--congress', String(congressNumber))
    } else if (source === 'openstates' && state) {
      args.push('openstates', '--state', state)
    }

    // Return job ID immediately - in a real implementation, this would use a job queue
    const jobId = `job-${Date.now()}`

    // Spawn the Python process (non-blocking)
    const pythonProcess = spawn('python3', args, {
      cwd: projectRoot,
      detached: true,
      stdio: 'ignore'
    })

    pythonProcess.unref()

    return NextResponse.json({
      success: true,
      jobId,
      message: 'Ingestion job started',
      command: `python3 ${args.join(' ')}`
    })

  } catch (error) {
    console.error('Ingestion API error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  // Get status of ingestion jobs
  const searchParams = request.nextUrl.searchParams
  const jobId = searchParams.get('jobId')

  // In a real implementation, this would check job status from a database or job queue
  return NextResponse.json({
    jobId,
    status: 'running',
    progress: 0.5,
    message: 'Job status tracking not yet implemented'
  })
}
