import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { api } from "./_generated/api";

// Convex stellt process.env zur Verfügung
declare const process: { env: Record<string, string | undefined> };

const http = httpRouter();

// Simple test route
http.route({
  path: "/api/ping",
  method: "GET",
  handler: httpAction(async () => {
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }),
});

// GET /api/leads
http.route({
  path: "/api/leads",
  method: "GET",
  handler: httpAction(async (ctx, request) => {
    const apiKey = request.headers.get("X-API-Key");
    if (apiKey !== process.env.MANNILEADS_API_KEY) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }
    const leads = await ctx.runQuery(api.leads.list);
    return new Response(JSON.stringify({ leads, count: leads.length }), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }),
});

// POST /api/leads/bulk
http.route({
  path: "/api/leads/bulk",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const apiKey = request.headers.get("X-API-Key");
    if (apiKey !== process.env.MANNILEADS_API_KEY) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }
    const { leads } = await request.json();
    const ids = await ctx.runMutation(api.leads.bulkCreate, { leads });
    return new Response(JSON.stringify({ ids }), {
      status: 201,
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
      },
    });
  }),
});

// OPTIONS for CORS
http.route({
  path: "/api/leads",
  method: "OPTIONS",
  handler: httpAction(async () => {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-API-Key",
      },
    });
  }),
});

http.route({
  path: "/api/leads/bulk",
  method: "OPTIONS",
  handler: httpAction(async () => {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-API-Key",
      },
    });
  }),
});

export default http;
