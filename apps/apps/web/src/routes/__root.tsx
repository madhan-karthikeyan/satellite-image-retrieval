import { Toaster } from "@satellite/ui/components/sonner";
import { Outlet, createRootRouteWithContext } from "@tanstack/react-router";
import type { QueryClient } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { useEffect, useState } from "react";

import Header from "@/components/header";
import "../index.css";
import { api } from "@/utils/api";

interface RouterAppContext {
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterAppContext>()({
  component: RootComponent,
  head: () => ({
    meta: [
      { title: "Satellite Visual Search" },
      { name: "description", content: "Visual Search, Retrieval & Detection in Satellite Imageries" },
    ],
    links: [
      { rel: "icon", href: "/favicon.ico" },
    ],
  }),
});

function RootComponent() {
  const [apiStatus, setApiStatus] = useState<"checking" | "connected" | "disconnected">("checking");

  useEffect(() => {
    const checkApi = async () => {
      try {
        await api.healthCheck();
        setApiStatus("connected");
      } catch {
        setApiStatus("disconnected");
      }
    };

    checkApi();
    const interval = setInterval(checkApi, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header apiStatus={apiStatus} />
      <main className="container mx-auto px-4 py-6">
        <Outlet />
      </main>
      <Toaster richColors position="bottom-right" />
      <TanStackRouterDevtools position="bottom-left" />
      <ReactQueryDevtools position="bottom" buttonPosition="bottom-right" />
    </div>
  );
}
