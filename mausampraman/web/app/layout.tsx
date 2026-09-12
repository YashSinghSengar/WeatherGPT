import "./globals.css";
import Navbar from "../components/Navbar";

export const metadata = { title: "MausamPraman — Weather intelligence you can trust" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main className="wrap">{children}</main>
        <footer className="footer"><div className="wrap">MausamPraman · Smart India Hackathon 2026 · deterministic trust first, AI wording only.</div></footer>
      </body>
    </html>
  );
}
