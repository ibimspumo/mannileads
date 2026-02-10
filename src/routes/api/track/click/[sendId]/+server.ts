import { ConvexHttpClient } from "convex/browser";
import { api } from "$lib/convex";
import { redirect } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
const CONVEX_URL = "https://energetic-civet-402.convex.cloud";

export const GET: RequestHandler = async ({ params, url, request, getClientAddress }) => {
  const { sendId } = params;
  const targetUrl = url.searchParams.get("url");

  if (!targetUrl) {
    throw redirect(302, "/");
  }

  try {
    // Initialize Convex client
    const client = new ConvexHttpClient(CONVEX_URL);

    // Log click event
    await client.mutation(api.email.createEvent, {
      sendId: sendId as any,
      type: "click",
      metadata: JSON.stringify({
        url: targetUrl,
        userAgent: request.headers.get("user-agent"),
        ip: getClientAddress(),
        timestamp: new Date().toISOString(),
      }),
    });
  } catch (error) {
    console.error("Failed to track click:", error);
    // Don't fail the redirect - still send user to target
  }

  // Redirect to original URL
  throw redirect(302, targetUrl);
};
