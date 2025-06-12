import './globals.css';

export const metadata = {
  title: 'Blog to Podcast Converter',
  description: 'Convert your blog posts into engaging podcasts',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">{children}</body>
    </html>
  )
}