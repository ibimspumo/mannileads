"use node";
import { v } from "convex/values";
import { action } from "./_generated/server";
import { api, internal } from "./_generated/api";

// ===== TEST SMTP CONNECTION =====

export const testConnection = action({
  args: { id: v.id("emailAccounts") },
  handler: async (ctx, args) => {
    const account: any = await ctx.runQuery(api.email.getAccount, { id: args.id });
    if (!account) {
      return { success: false, error: "Account nicht gefunden" };
    }

    try {
      const nodemailerModule = await import("nodemailer");
      const nodemailer = nodemailerModule.default || nodemailerModule;

      const transporter = nodemailer.createTransport({
        host: account.smtpHost,
        port: account.smtpPort,
        secure: account.smtpPort === 465,
        auth: {
          user: account.smtpUser,
          pass: account.smtpPassword,
        },
        tls: {
          rejectUnauthorized: true,
        },
      });

      await transporter.verify();

      return {
        success: true,
        message: `SMTP-Verbindung zu ${account.smtpHost}:${account.smtpPort} erfolgreich`,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.message || "Unbekannter Fehler",
      };
    }
  },
});
