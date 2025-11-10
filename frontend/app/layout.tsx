import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'OpenLegislation - Data Ingestion Platform',
  description: 'Advanced data ingestion and management platform for legislative data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <div className="min-h-screen bg-gray-50">
          {children}
        </div>
      </body>
    </html>
  )
}