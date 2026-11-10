import { PortalShell } from "@/components/portal-shell";
import { AdminDashboard } from "@/features/admin/dashboard";

export default function AdminPortalPlaceholder() {
  return <PortalShell title="Admin portal"><AdminDashboard /></PortalShell>;
}
