import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import path from 'path'

export async function GET(request: NextRequest) {
  try {
    const projectRoot = path.resolve(process.cwd(), '..')
    const logPath = path.join(projectRoot, 'tools', 'ingestion_log.json')
    
    try {
      const logData = await readFile(logPath, 'utf-8')
      const logs = JSON.parse(logData)
      
      return NextResponse.json({
        success: true,
        logs
      })
    } catch (fileError) {
      // If file doesn't exist, return empty logs
      return NextResponse.json({
        success: true,
        logs: {},
        message: 'No ingestion logs found yet'
      })
    }

  } catch (error) {
    console.error('Logs fetch error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      },
      { status: 500 }
    )
  }
}
