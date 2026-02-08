import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { api } from "./_generated/api";

// Convex Runtime stellt process.env bereit
declare const process: { env: Record<string, string | undefined> };

const http = httpRouter();

// Hilfsfunktion: API Key prüfen
async function checkApiKey(ctx: any, request: Request): Promise<Response | null> {
  const apiKey = request.headers.get("X-API-Key");
  const expected = process.env.MANNILEADS_API_KEY;
  if (!expected || apiKey !== expected) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }
  return null;
}

// CORS Headers
function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-API-Key",
    "Content-Type": "application/json",
  };
}

// OPTIONS für CORS Preflight
http.route({
  path: "/api/leads",
  method: "OPTIONS",
  handler: httpAction(async () => {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }),
});

http.route({
  path: "/api/leads/bulk",
  method: "OPTIONS",
  handler: httpAction(async () => {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }),
});

// GET /api/leads - Alle Leads abrufen
http.route({
  path: "/api/leads",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const authError = await checkApiKey(ctx, request);
    if (authError) return authError;

    const leads = await ctx.runQuery(api.leads.list);
    return new Response(JSON.stringify({ leads }), {
      status: 200,
      headers: corsHeaders(),
    });
  }),
});

// POST /api/leads - Neuen Lead erstellen
http.route({
  path: "/api/leads",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const authError = await checkApiKey(ctx, request);
    if (authError) return authError;

    try {
      const body = await request.json();
      const id = await ctx.runMutation(api.leads.create, body);
      return new Response(JSON.stringify({ id }), {
        status: 201,
        headers: corsHeaders(),
      });
    } catch (e: any) {
      return new Response(JSON.stringify({ error: e.message }), {
        status: 400,
        headers: corsHeaders(),
      });
    }
  }),
});

// POST /api/leads/bulk - Mehrere Leads erstellen
http.route({
  path: "/api/leads/bulk",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const authError = await checkApiKey(ctx, request);
    if (authError) return authError;

    try {
      const { leads } = await request.json();
      const ids = await ctx.runMutation(api.leads.bulkCreate, { leads });
      return new Response(JSON.stringify({ ids }), {
        status: 201,
        headers: corsHeaders(),
      });
    } catch (e: any) {
      return new Response(JSON.stringify({ error: e.message }), {
        status: 400,
        headers: corsHeaders(),
      });
    }
  }),
});

// PATCH /api/leads - Lead updaten (ID im Body)
http.route({
  path: "/api/leads",
  method: "PATCH",
  handler: httpAction(async (ctx, request) => {
    const authError = await checkApiKey(ctx, request);
    if (authError) return authError;

    try {
      const body = await request.json();
      await ctx.runMutation(api.leads.update, body);
      return new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: corsHeaders(),
      });
    } catch (e: any) {
      return new Response(JSON.stringify({ error: e.message }), {
        status: 400,
        headers: corsHeaders(),
      });
    }
  }),
});

export default http;
