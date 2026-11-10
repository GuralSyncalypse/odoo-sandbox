import { PortalShell } from "@/components/portal-shell";
import { UserDashboard } from "@/features/user/dashboard";

export default function UserPortalPlaceholder() {
  return <PortalShell title="User portal"><UserDashboard /></PortalShell>;
}
