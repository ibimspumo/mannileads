<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { convex, api } from '$lib/convex';
	import EmailTemplateEditor from '$lib/components/email/EmailTemplateEditor.svelte';

	let templateId = $derived(page.params.id);
	let name = $state('');
	let subject = $state('');
	let htmlBody = $state('');
	let rawBody = $state('');
	let saving = $state(false);
	let loading = $state(true);

	const EXAMPLE_DATA: Record<string, string> = {
		firma: 'Musterfirma GmbH',
		email: 'info@musterfirma.de',
		ansprechpartner: 'Max Mustermann',
		position: 'Geschäftsführer',
		telefon: '0385 123456',
		strasse: 'Schloßstraße 1',
		plz: '19053',
		ort: 'Schwerin',
		bundesland: 'Mecklenburg-Vorpommern',
		branche: 'Gastronomie',
		groesse: 'Klein (1-10)',
		website: 'www.musterfirma.de',
		websiteQualitaet: '45',
		socialMediaLinks: 'facebook.com/musterfirma',
		googleBewertung: '4.2 (38 Bewertungen)',
		score: '75',
		segment: 'HOT',
		kiScore: '82',
		kiSegment: 'HOT',
		kiScoreBegruendung: 'Hohe lokale Relevanz, ausbaufähiger Online-Auftritt',
		kiZusammenfassung: 'Etabliertes Restaurant in der Schweriner Altstadt mit gutem Ruf aber schwacher Online-Präsenz.',
		kiAnsprache: 'Ihr Restaurant hat top Google-Bewertungen, aber online verschenken Sie Potenzial. Wir bringen Ihre Sichtbarkeit auf das Level, das Ihre Küche verdient.',
		kiAnspracheSig: 'Mit über 10.000 Lesern monatlich erreicht Schwerin ist Geil genau Ihre Zielgruppe — Schweriner, die gerne ausgehen.',
		kiZielgruppe: 'Lokale Feinschmecker, Touristen, Geschäftsessen',
		kiOnlineAuftritt: 'Website veraltet (kein Responsive Design), Social Media inaktiv seit 6 Monaten',
		kiSchwaechen: 'Keine Online-Reservierung, Social Media vernachlässigt, Website nicht mobiloptimiert',
		kiChancen: 'Social Media Relaunch, Google Business optimieren, Online-Reservierung einrichten',
		kiWettbewerb: '3 ähnliche Restaurants im Umkreis, alle mit besserer Online-Präsenz',
		status: 'Neu',
		tags: 'Restaurant, Altstadt, Premium',
		notizen: '',
	};

	let previewHtml = $derived(
		(rawBody || htmlBody).replace(/\{\{(\w+)\}\}/g, (_, key) => EXAMPLE_DATA[key] || `{{${key}}}`)
	);

	let previewSubject = $derived(
		subject.replace(/\{\{(\w+)\}\}/g, (_, key) => EXAMPLE_DATA[key] || `{{${key}}}`)
	);

	let usedPlaceholders = $derived(
		[...new Set(((rawBody || htmlBody) + ' ' + subject).match(/\{\{(\w+)\}\}/g)?.map(m => m.replace(/[{}]/g, '')) || [])]
	);

	onMount(async () => {
		try {
			const tmpl = await convex.query(api.email.getTemplate, { id: templateId as any });
			if (tmpl) {
				name = tmpl.name;
				subject = tmpl.subject;
				// Strip email wrapper if present, get inner body content
				const match = tmpl.htmlBody?.match(/<td[^>]*style="padding:30px 40px[^"]*"[^>]*>([\s\S]*?)<\/td>/);
				htmlBody = match ? match[1].trim() : (tmpl.htmlBody || '');
			}
		} catch (e) {
			console.error('Load failed:', e);
		} finally {
			loading = false;
		}
	});

	function wrapEmailHtml(body: string): string {
		return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;">
<tr><td align="center" style="padding:20px 0;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:4px;overflow:hidden;max-width:600px;width:100%;">
<tr><td style="padding:30px 40px;font-size:15px;line-height:1.6;color:#333333;">
${body}
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>`;
	}

	async function save() {
		if (!name || !subject) return alert('Name und Betreff sind Pflicht!');
		saving = true;
		try {
			await convex.mutation(api.email.updateTemplate, {
				id: templateId as any,
				name,
				subject,
				htmlBody: wrapEmailHtml(rawBody || htmlBody),
				placeholders: usedPlaceholders,
			});
			goto('/email/templates');
		} catch (e) {
			console.error('Save failed:', e);
			alert('Fehler: ' + e);
		} finally {
			saving = false;
		}
	}

	function insertPlaceholderInSubject(key: string) {
		subject += `{{${key}}}`;
	}
</script>

<div class="space-y-6 animate-fade-in">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold font-mono tracking-tight text-[var(--color-accent)]">
				TEMPLATE BEARBEITEN
			</h1>
			<p class="text-sm text-[var(--color-text-muted)] mt-1">{name || 'Lade...'}</p>
		</div>
		<a href="/email/templates" class="px-3 py-1.5 text-xs font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded transition-all">
			← ZURÜCK
		</a>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="text-sm text-[var(--color-text-muted)] animate-pulse font-mono">LADE TEMPLATE...</div>
		</div>
	{:else}
		<div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
			<div class="space-y-4">
				<div class="panel">
					<div class="panel-header">Einstellungen</div>
					<div class="p-4 space-y-4">
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Template-Name *</label>
							<input bind:value={name} class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none" />
						</div>
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Betreff *</label>
							<input bind:value={subject} class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none font-mono" />
							<div class="flex flex-wrap gap-1 mt-2">
								{#each ['firma', 'ansprechpartner', 'ort', 'branche'] as key}
									<button class="px-1.5 py-0.5 text-[10px] font-mono bg-[var(--color-surface-600)] text-[var(--color-accent)] rounded hover:bg-[var(--color-surface-500)] transition-colors" onclick={() => insertPlaceholderInSubject(key)}>
										+{`{{${key}}}`}
									</button>
								{/each}
							</div>
						</div>
					</div>
				</div>

				<div class="panel">
					<div class="panel-header">
						<div class="flex items-center gap-4">
							<span>Email-Inhalt</span>
							{#if usedPlaceholders.length > 0}
								<div class="flex flex-wrap gap-1">
									{#each usedPlaceholders as ph}
										<span class="px-1.5 py-0.5 text-[10px] font-mono bg-[var(--color-surface-600)] text-[var(--color-accent)] rounded">{`{{${ph}}}`}</span>
									{/each}
								</div>
							{/if}
						</div>
					</div>
					<div class="p-2">
						<EmailTemplateEditor content={htmlBody} onchange={(html) => rawBody = html} />
					</div>
				</div>

				<div class="flex gap-2">
					<button onclick={save} disabled={saving || !name || !subject} class="px-4 py-2 text-sm font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed text-[var(--color-surface-900)] rounded transition-all shadow-[0_0_12px_rgba(255,165,2,0.3)]">
						{saving ? 'SPEICHERE...' : 'ÄNDERUNGEN SPEICHERN'}
					</button>
					<a href="/email/templates" class="px-4 py-2 text-sm font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] rounded transition-all">
						ABBRECHEN
					</a>
				</div>
			</div>

			<div class="panel sticky top-4">
				<div class="panel-header">
					<div class="flex items-center justify-between w-full">
						<span>Vorschau</span>
						<span class="text-[10px] text-[var(--color-text-muted)] font-normal">mit Beispieldaten</span>
					</div>
				</div>
				<div class="p-4 space-y-3">
					{#if subject}
						<div>
							<div class="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Betreff</div>
							<div class="text-sm font-medium text-[var(--color-text-primary)] bg-[var(--color-surface-700)] px-3 py-2 rounded font-mono">{previewSubject}</div>
						</div>
					{/if}
					<div>
						<div class="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Email-Body</div>
						<div class="bg-white rounded overflow-hidden border border-[var(--color-surface-600)]">
							<iframe title="Email Preview" srcdoc={wrapEmailHtml(previewHtml)} class="w-full min-h-[400px] border-0" sandbox=""></iframe>
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
