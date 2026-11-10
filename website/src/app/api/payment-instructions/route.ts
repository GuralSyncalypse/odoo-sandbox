import { NextResponse } from "next/server";
import { getConfig } from "@/server/config";

export async function GET() {
  const config = getConfig();
  return NextResponse.json({ qrImageUrl: config.vietQrImageUrl, instructions: config.bankInstructions });
}
