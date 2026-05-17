import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 flex flex-col">
      <header className="flex items-center justify-between px-8 py-5 border-b bg-white">
        <div className="font-semibold text-lg">CampusConnect</div>
        <nav className="flex gap-2">
          <Link href="/login"><Button variant="ghost">Log in</Button></Link>
          <Link href="/signup"><Button>Get started</Button></Link>
        </nav>
      </header>
      <section className="flex-1 flex items-center justify-center p-12">
        <div className="max-w-2xl text-center space-y-6">
          <h1 className="text-5xl font-semibold tracking-tight">An AI WhatsApp admissions team that never sleeps.</h1>
          <p className="text-lg text-slate-600">
            CampusConnect captures, qualifies, nurtures, and hands over admission leads
            for educational institutes — on WhatsApp, in any language your students speak.
          </p>
          <div className="flex gap-3 justify-center">
            <Link href="/signup"><Button size="lg">Start free</Button></Link>
            <Link href="/demo"><Button size="lg" variant="outline">See it live</Button></Link>
          </div>
        </div>
      </section>
    </main>
  );
}
