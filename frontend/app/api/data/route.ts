import { NextRequest, NextResponse } from 'next/server'
import { Pool } from 'pg'

// Database connection - in production, use environment variables
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'openleg',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'password'
})

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const table = searchParams.get('table') || 'bill'
    const limit = parseInt(searchParams.get('limit') || '100')
    const offset = parseInt(searchParams.get('offset') || '0')
    
    // Build WHERE clause from filters
    const filters: string[] = []
    const values: any[] = []
    let paramIndex = 1

    // Congress number filter
    const congressNumber = searchParams.get('congressNumber')
    if (congressNumber) {
      filters.push(`federal_congress = $${paramIndex}`)
      values.push(parseInt(congressNumber))
      paramIndex++
    }

    // Session year filter
    const sessionYear = searchParams.get('sessionYear')
    if (sessionYear) {
      filters.push(`bill_session_year = $${paramIndex}`)
      values.push(parseInt(sessionYear))
      paramIndex++
    }

    // State filter
    const state = searchParams.get('state')
    if (state) {
      filters.push(`state = $${paramIndex}`)
      values.push(state)
      paramIndex++
    }

    // Date range filters
    const startDate = searchParams.get('startDate')
    if (startDate) {
      filters.push(`created_date_time >= $${paramIndex}`)
      values.push(startDate)
      paramIndex++
    }

    const endDate = searchParams.get('endDate')
    if (endDate) {
      filters.push(`created_date_time <= $${paramIndex}`)
      values.push(endDate)
      paramIndex++
    }

    // Text search filter
    const searchText = searchParams.get('search')
    if (searchText) {
      filters.push(`(title ILIKE $${paramIndex} OR summary ILIKE $${paramIndex})`)
      values.push(`%${searchText}%`)
      paramIndex++
    }

    const whereClause = filters.length > 0 ? `WHERE ${filters.join(' AND ')}` : ''
    
    // Get table schema for safer querying
    const validTables = ['bill', 'federal_bills', 'federal_members', 'member', 'committee', 'vote']
    const safeTable = validTables.includes(table) ? `master.${table}` : 'master.bill'

    const query = `
      SELECT * FROM ${safeTable}
      ${whereClause}
      ORDER BY created_date_time DESC
      LIMIT $${paramIndex} OFFSET $${paramIndex + 1}
    `
    
    values.push(limit, offset)

    const result = await pool.query(query, values)

    return NextResponse.json({
      success: true,
      data: result.rows,
      count: result.rowCount,
      offset,
      limit
    })

  } catch (error) {
    console.error('Data fetch error:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error',
        message: 'Database connection may not be configured. Using mock data for demonstration.'
      },
      { status: 200 } // Return 200 with error message for demo purposes
    )
  }
}
