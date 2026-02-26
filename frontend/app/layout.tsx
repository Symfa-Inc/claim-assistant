import '@/app/ui/global.css'
import { plusJakarta } from '@/app/ui/fonts';


export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${plusJakarta.variable} ${plusJakarta.className} antialiased`}>
        {children}
      </body>
    </html>
  );
}
