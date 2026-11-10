import { redirect } from "next/navigation";
import { getSession } from "@/server/auth/session";

export default async function AdminLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const session = await getSession();
  if (!session?.isAdmin) redirect("/");
  return <section data-portal="admin">{children}</section>;
}
