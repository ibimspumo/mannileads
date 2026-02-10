import { ConvexHttpClient } from "convex/browser";

const CONVEX_URL = process.env.VITE_CONVEX_URL || process.env.PUBLIC_CONVEX_URL;
if (!CONVEX_URL) {
  // Try reading from .env.local
  const fs = await import('fs');
  const envFile = fs.readFileSync('.env.local', 'utf8');
  const match = envFile.match(/(?:VITE_CONVEX_URL|PUBLIC_CONVEX_URL)=(.+)/);
  if (!match) { console.error('No CONVEX_URL found'); process.exit(1); }
  var url = match[1].trim();
} else {
  var url = CONVEX_URL;
}

const client = new ConvexHttpClient(url);

const SIG_SIGNATURE_HTML = `
<table cellpadding="0" cellspacing="0" border="0" style="font-family: Georgia, 'Times New Roman', serif; max-width: 400px;">
  <tr>
    <td style="padding: 16px 0 0 0; border-top: 3px solid #dc2626;">
      <table cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td style="padding-right: 16px; vertical-align: top;">
            <div style="width: 48px; height: 48px; background-color: #dc2626; border-radius: 4px; text-align: center; line-height: 48px;">
              <span style="color: #ffffff; font-size: 20px; font-weight: 900; font-family: Georgia, serif;">S</span>
            </div>
          </td>
          <td style="vertical-align: top;">
            <div style="font-size: 16px; font-weight: 900; color: #1a1a18; font-family: Georgia, 'Times New Roman', serif; line-height: 1.2;">
              Schwerin <span style="color: #dc2626;">ist Geil</span>
            </div>
            <div style="font-size: 11px; color: #8a8680; font-family: -apple-system, Arial, sans-serif; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 2px;">
              Die geilste Nachrichtenquelle
            </div>
            <div style="margin-top: 8px;">
              <a href="https://schwerinistgeil.de" style="color: #dc2626; font-size: 12px; font-family: -apple-system, Arial, sans-serif; text-decoration: none; font-weight: 600;">schwerinistgeil.de</a>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
`.trim();

// Check if SIG account already exists
const { api } = await import("../convex/_generated/api.js");

const accounts = await client.query(api.email.listAccounts);
const sigAccount = accounts.find(a => a.fromEmail?.includes('schwerinistgeil'));

if (sigAccount) {
  console.log('SIG account found, updating signature...');
  await client.mutation(api.email.updateAccount, {
    id: sigAccount._id,
    signatureHtml: SIG_SIGNATURE_HTML,
  });
  console.log('✅ Signature updated for:', sigAccount.fromEmail);
} else {
  console.log('No SIG account found, creating one...');
  const id = await client.mutation(api.email.createAccount, {
    name: 'Schwerin ist Geil',
    fromEmail: 'kontakt@schwerinistgeil.de',
    fromName: 'Schwerin ist Geil',
    signatureHtml: SIG_SIGNATURE_HTML,
    sesAccessKey: 'PLACEHOLDER',
    sesSecretKey: 'PLACEHOLDER',
    sesRegion: 'eu-central-1',
  });
  console.log('✅ SIG account created with ID:', id);
}
