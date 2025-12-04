import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { Providers } from './providers'
import { MainLayout } from '@/components/common/MainLayout'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'UNS Kobetsu Keiyakusho | 個別契約書管理システム',
  description: '労働者派遣法第26条に準拠した個別契約書管理システム',
  keywords: ['派遣契約', '個別契約書', '労働者派遣法', 'UNS企画'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const mode = localStorage.getItem('theme-mode') || 'light';
                if (mode === 'dark') {
                  document.documentElement.classList.add('dark');
                } else if (mode === 'system') {
                  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                  if (prefersDark) {
                    document.documentElement.classList.add('dark');
                  }
                }

                const theme = localStorage.getItem('theme') || 'blue';
                document.documentElement.setAttribute('data-theme', theme);
              } catch {}
            `,
          }}
        />
      </head>
      <body className={`${inter.className} antialiased`}>
        <Providers>
          <MainLayout>
            {children}
          </MainLayout>
        </Providers>
      </body>
    </html>
  )
}
