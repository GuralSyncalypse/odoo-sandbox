import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Telesales Portal",
  description: "Website gateway for the telesales allocation system.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="vi"><body>{children}</body></html>;
}
