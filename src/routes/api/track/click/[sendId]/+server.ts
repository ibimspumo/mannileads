import { ConvexHttpClient } from "convex/browser";
import { api } from "$lib/convex/_generated/api";
import { redirect } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { PUBLIC_CONVEX_URL } from "$env/static/public";

export const GET: RequestHandler = async ({ params, url, request, getClientAddress }) => {
  const { sendId } = params;
  const targetUrl = url.searchParams.get("url");

  if (!targetUrl) {
    throw redirect(302, "/");
  }

  try {
    // Initialize Convex client
    const client = new ConvexHttpClient(PUBLIC_CONVEX_URL);

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
