import { redirect } from "next/navigation";
import { getSession } from "@/server/auth/session";

export default async function UserLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  if (!await getSession()) redirect("/");
  return <section data-portal="user">{children}</section>;
}
