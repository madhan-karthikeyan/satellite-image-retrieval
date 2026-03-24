import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Zap,
  Cpu,
  Database,
  Settings,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { api, type HealthResponse } from "@/utils/api";

export const Route = createFileRoute("/status")({
  component: StatusComponent,
});

function StatusComponent() {
  const { data: health, isLoading: healthLoading } = useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: () => api.healthCheck(),
    refetchInterval: 5000,
  });

  const { data: searchStatus, isLoading: statusLoading } = useQuery({
    queryKey: ["searchStatus"],
    queryFn: () => api.getSearchStatus(),
    refetchInterval: 10000,
  });

  if (healthLoading || statusLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          System Status
        </h1>
        <p className="text-muted-foreground mt-1">
          Monitor the health and configuration of the visual search engine
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <StatusCard
          icon={<Zap className="w-5 h-5" />}
          title="API Status"
          items={[
            {
              label: "Health",
              value: health?.status === "healthy" ? "Healthy" : "Unhealthy",
              status: health?.status === "healthy" ? "success" : "error",
            },
            {
              label: "Embedding Model",
              value: health?.embedding_model || "Unknown",
            },
            {
              label: "Device",
              value: health?.device || "Unknown",
            },
            {
              label: "ChromaDB",
              value: health?.chroma_available ? "Available" : "Unavailable",
              status: health?.chroma_available ? "success" : "error",
            },
          ]}
        />

        <StatusCard
          icon={<Settings className="w-5 h-5" />}
          title="Search Configuration"
          items={[
            {
              label: "Status",
              value: searchStatus?.status || "Unknown",
              status: searchStatus?.status === "ready" ? "success" : "warning",
            },
            {
              label: "Total Chips",
              value: String(searchStatus?.total_chips || 0),
            },
            {
              label: "Search Threshold",
              value: searchStatus?.search_threshold?.toFixed(2) || "N/A",
            },
            {
              label: "Window Sizes",
              value: searchStatus?.sliding_window_sizes?.map(String).join(", ") || "N/A",
            },
          ]}
        />
      </div>

      <StatusCard
        icon={<Database className="w-5 h-5" />}
        title="Available Object Classes"
        className="md:col-span-2"
      >
        {searchStatus?.available_objects && searchStatus.available_objects.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {searchStatus.available_objects.map((obj) => (
              <span
                key={obj}
                className="px-3 py-1.5 rounded-lg bg-primary/20 text-primary text-sm font-medium"
              >
                {obj}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">No object classes available</p>
        )}
      </StatusCard>

      <div className="rounded-2xl border bg-gradient-to-br from-primary/10 to-accent/10 p-6">
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-primary" />
          Quick Reference
        </h3>
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <p className="text-muted-foreground">Object Classes (Stage-1):</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Playground</li>
              <li>Brick Kiln</li>
              <li>Metro Shed</li>
              <li>Pond-1 (Dried)</li>
              <li>Pond-2 (Filled)</li>
            </ul>
          </div>
          <div className="space-y-2">
            <p className="text-muted-foreground">Additional Classes:</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              <li>Sheds</li>
              <li>Solar Panel</li>
              <li>STP (Sewerage Treatment Plant)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusCard({
  icon,
  title,
  items,
  children,
  className = "",
}: {
  icon: React.ReactNode;
  title: string;
  items?: Array<{
    label: string;
    value: string;
    status?: "success" | "error" | "warning";
  }>;
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-2xl border bg-card p-6 ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-primary">{icon}</span>
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>

      {items && (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{item.label}</span>
              <div className="flex items-center gap-2">
                {item.status && (
                  item.status === "success" ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  ) : item.status === "error" ? (
                    <XCircle className="w-4 h-4 text-destructive" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-yellow-500" />
                  )
                )}
                <span className="text-sm font-medium">{item.value}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {children}
    </div>
  );
}
