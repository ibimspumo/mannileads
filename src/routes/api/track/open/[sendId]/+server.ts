import { ConvexHttpClient } from "convex/browser";
import { api } from "$lib/convex";
import type { RequestHandler } from "./$types";
const CONVEX_URL = "https://energetic-civet-402.convex.cloud";

// 1x1 transparent GIF
const TRACKING_PIXEL = Buffer.from(
  "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
  "base64"
);

export const GET: RequestHandler = async ({ params, request, getClientAddress }) => {
  const { sendId } = params;

  try {
    // Initialize Convex client
    const client = new ConvexHttpClient(CONVEX_URL);

    // Log open event
    await client.mutation(api.email.createEvent, {
      sendId: sendId as any,
      type: "open",
      metadata: JSON.stringify({
        userAgent: request.headers.get("user-agent"),
        ip: getClientAddress(),
        timestamp: new Date().toISOString(),
      }),
    });
  } catch (error) {
    console.error("Failed to track open:", error);
    // Don't fail the request - still return the pixel
  }

  // Return 1x1 transparent GIF
  return new Response(TRACKING_PIXEL, {
    headers: {
      "Content-Type": "image/gif",
      "Cache-Control": "no-cache, no-store, must-revalidate",
      Pragma: "no-cache",
      Expires: "0",
    },
  });
};
