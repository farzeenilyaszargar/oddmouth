import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = { title: 'Oddmouth — Small model. Big mouth.', description: 'A little text. A little voice. Oddmouth is building free, simple text to speech for everyone. Try the five-second demo.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
