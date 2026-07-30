import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/providers'
import { DashboardLayout } from '@/components/layout/dashboard-layout'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AutoDocOps - AI Platform',
  description: 'Production-grade AI platform for automated documentation operations',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <DashboardLayout>{children}</DashboardLayout>
        </Providers>
      </body>
    </html>
  )
}
