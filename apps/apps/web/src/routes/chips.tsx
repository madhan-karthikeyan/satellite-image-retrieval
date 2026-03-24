import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Database, Trash2, Loader2, RefreshCw } from "lucide-react";
import { api } from "@/utils/api";

export const Route = createFileRoute("/chips")({
  component: ChipsComponent,
});

function ChipsComponent() {
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["chips"],
    queryFn: () => api.listChips(),
    refetchInterval: 10000,
  });

  const deleteMutation = useMutation({
    mutationFn: (objectName: string) => api.deleteChips(objectName),
    onSuccess: () => {
      toast.success("Chips deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["chips"] });
    },
    onError: (error) => {
      toast.error(`Failed to delete: ${error}`);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-20 text-destructive">
        Failed to load chips. Please check API connection.
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Image Chips
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage uploaded reference chips for visual search
          </p>
        </div>
        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ["chips"] })}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary hover:bg-secondary/80 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <div className="rounded-2xl border bg-card">
        <div className="p-4 border-b border-border/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-primary" />
            <span className="font-semibold">Total Chips: {data?.total_chips || 0}</span>
          </div>
        </div>

        {data?.chips && data.chips.length > 0 ? (
          <div className="divide-y divide-border/50">
            {data.chips.map((chip) => (
              <div
                key={chip.object_name}
                className="p-4 flex items-center justify-between hover:bg-secondary/30 transition-colors"
              >
                <div>
                  <p className="font-medium">{chip.object_name}</p>
                  <p className="text-sm text-muted-foreground">
                    {chip.count} chip{chip.count !== 1 ? "s" : ""} uploaded
                  </p>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(chip.object_name)}
                  disabled={deleteMutation.isPending}
                  className="p-2 rounded-lg hover:bg-destructive/20 text-destructive transition-colors disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center text-muted-foreground">
            <Database className="w-12 h-12 mx-auto mb-4 opacity-30" />
            <p>No image chips uploaded yet</p>
            <p className="text-sm">Upload chips from the search page</p>
          </div>
        )}
      </div>
    </div>
  );
}
