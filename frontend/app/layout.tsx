import '../styles/globals.css'; // Исправленный путь

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">
        <header className="bg-white shadow py-4">
          <div className="container mx-auto px-4">
            <h1 className="text-2xl font-bold">Learning Center</h1>
          </div>
        </header>
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  )
}
