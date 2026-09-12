"use client";
import { useState } from "react";
import Link from "next/link";

export default function Navbar() {
  const [open, setOpen] = useState(false);
  return (
    <nav className="nav" aria-label="Main">
      <div className="nav-inner">
        <Link href="/" className="brand">MausamPraman</Link>
        <button className="menu-btn" aria-label="Toggle menu" aria-expanded={open} onClick={() => setOpen(!open)}>☰</button>
        <div className={`nav-links${open ? " open" : ""}`}>
          <Link href="/" onClick={() => setOpen(false)}>Home</Link>
          <Link href="/chat" onClick={() => setOpen(false)}>Chat</Link>
          <Link href="/how-it-works" onClick={() => setOpen(false)}>How It Works</Link>
          <Link href="/about" onClick={() => setOpen(false)}>About</Link>
          <Link href="/chat" className="btn" onClick={() => setOpen(false)}>Ask MausamPraman</Link>
        </div>
      </div>
    </nav>
  );
}
