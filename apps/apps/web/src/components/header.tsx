import { Link } from "@tanstack/react-router";
import { Satellite, Zap, Database, Search } from "lucide-react";
import { ModeToggle } from "./mode-toggle";

interface HeaderProps {
  apiStatus: "checking" | "connected" | "disconnected";
}

export default function Header({ apiStatus }: HeaderProps) {
  return (
    <header className="border-b border-border/50 bg-card/80 backdrop-blur-xl sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center group-hover:scale-105 transition-transform">
                <Satellite className="w-5 h-5 text-primary-foreground" />
              </div>
              <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 to-accent/20 rounded-xl blur opacity-0 group-hover:opacity-100 transition-opacity -z-10" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold tracking-tight">
                <span className="text-primary">Sat</span>
                <span className="text-foreground">Vision</span>
              </span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest">
                Visual Search Engine
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <NavItem icon={<Search className="w-4 h-4" />} label="Search" to="/" />
            <NavItem icon={<Database className="w-4 h-4" />} label="Chips" to="/chips" />
            <NavItem icon={<Zap className="w-4 h-4" />} label="Status" to="/status" />
          </nav>

          <div className="flex items-center gap-4">
            <StatusIndicator status={apiStatus} />
            <ModeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}

function NavItem({
  icon,
  label,
  to,
}: {
  icon: React.ReactNode;
  label: string;
  to: string;
}) {
  return (
    <Link
      to={to}
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors"
    >
      {icon}
      {label}
    </Link>
  );
}

function StatusIndicator({
  status,
}: {
  status: "checking" | "connected" | "disconnected";
}) {
  const config = {
    checking: { color: "bg-yellow-500", label: "Checking...", pulse: true },
    connected: { color: "bg-emerald-500", label: "API Online", pulse: false },
    disconnected: { color: "bg-red-500", label: "API Offline", pulse: false },
  };

  const { color, label, pulse } = config[status];

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 text-xs font-medium">
      <div className={`w-2 h-2 rounded-full ${color} ${pulse ? "animate-pulse" : ""}`} />
      <span className="text-muted-foreground">{label}</span>
    </div>
  );
}
