import '@/app/ui/global.css'
import { plusJakarta, instrumentSerif } from '@/app/ui/fonts';


export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${plusJakarta.variable} ${instrumentSerif.variable} ${plusJakarta.className} antialiased`}>
        {children}
      </body>
    </html>
  );
}
