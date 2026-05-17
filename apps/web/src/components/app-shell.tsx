import Link from "next/link";

export function AppShell({ children, email }: { children: React.ReactNode; email: string }) {
  return (
    <div className="min-h-screen grid grid-cols-[240px_1fr] bg-slate-50">
      <aside className="bg-white border-r flex flex-col">
        <div className="px-6 py-5 font-semibold">CampusConnect</div>
        <nav className="flex-1 px-3 space-y-1 text-sm">
          <SidebarLink href="/app">Dashboard</SidebarLink>
          <SidebarLink href="/app/inbox">Inbox</SidebarLink>
          <SidebarLink href="/app/leads">Leads</SidebarLink>
          <SidebarLink href="/app/settings/organization">Settings</SidebarLink>
        </nav>
        <div className="border-t p-4 text-xs text-slate-500">Signed in as<br /><span className="text-slate-900">{email}</span></div>
      </aside>
      <main className="p-10">{children}</main>
    </div>
  );
}

function SidebarLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="block px-3 py-2 rounded hover:bg-slate-100 text-slate-700">
      {children}
    </Link>
  );
}
