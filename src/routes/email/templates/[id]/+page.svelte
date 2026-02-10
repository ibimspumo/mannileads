<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { convex, api } from '$lib/convex';
	import EmailTemplateEditor from '$lib/components/organisms/EmailTemplateEditor.svelte';

	// Available placeholders from Lead schema
	const placeholders = [
		'firma',
		'website',
		'branche',
		'groesse',
		'plz',
		'ort',
		'bundesland',
		'ansprechpartner',
		'position',
		'email',
		'telefon',
		'strasse',
		'score',
		'segment'
	];

	// Example data for preview
	const exampleData = {
		firma: 'Musterfirma GmbH',
		website: 'www.musterfirma.de',
		branche: 'Gastronomie',
		groesse: '10-50',
		plz: '19055',
		ort: 'Schwerin',
		bundesland: 'Mecklenburg-Vorpommern',
		ansprechpartner: 'Max Mustermann',
		position: 'Geschäftsführer',
		email: 'max@musterfirma.de',
		telefon: '+49 123 456789',
		strasse: 'Musterstraße 123',
		score: '75',
		segment: 'warm'
	};

	// State
	let templateId = $derived($page.params.id);
	let loading = $state(true);
	let saving = $state(false);
	let showPreview = $state(false);
	let template = $state<any>(null);

	// Form state
	let form = $state({
		name: '',
		subject: '',
		htmlBody: ''
	});

	onMount(async () => {
		await loadTemplate();
	});

	async function loadTemplate() {
		try {
			loading = true;
			template = await convex.query(api.email.getTemplate, { 
				id: templateId as any 
			});

			if (template) {
				// Unwrap HTML from email wrapper if present
				const unwrapped = unwrapEmailHtml(template.htmlBody);
				form = {
					name: template.name,
					subject: template.subject,
					htmlBody: unwrapped
				};
			}
		} catch (error) {
			console.error('Failed to load template:', error);
			alert('Fehler beim Laden: ' + error);
		} finally {
			loading = false;
		}
	}

	// Extract body from email wrapper
	function unwrapEmailHtml(html: string): string {
		// Try to extract content from .email-container div
		const match = html.match(/<div class="email-container">([\s\S]*?)<\/div>/);
		if (match) {
			return match[1].trim();
		}
		// If no wrapper found, return as-is
		return html;
	}

	// Render template with example data
	function renderPreview(template: string): string {
		let rendered = template;
		for (const [key, value] of Object.entries(exampleData)) {
			const regex = new RegExp(`{{${key}}}`, 'g');
			rendered = rendered.replace(regex, value);
		}
		return rendered;
	}

	async function saveTemplate() {
		if (!form.name || !form.subject || !form.htmlBody) {
			alert('Bitte alle Felder ausfüllen!');
			return;
		}

		try {
			saving = true;

			// Extract used placeholders
			const usedPlaceholders = placeholders.filter(
				(p) => form.subject.includes(`{{${p}}}`) || form.htmlBody.includes(`{{${p}}}`)
			);

			// Wrap HTML in email-compatible structure
			const emailHtml = wrapEmailHtml(form.htmlBody);

			await convex.mutation(api.email.updateTemplate, {
				id: templateId as any,
				name: form.name,
				subject: form.subject,
				htmlBody: emailHtml,
				placeholders: usedPlaceholders
			});

			goto('/email/templates');
		} catch (error) {
			console.error('Failed to save template:', error);
			alert('Fehler beim Speichern: ' + error);
		} finally {
			saving = false;
		}
	}

	// Wrap HTML in email-compatible wrapper
	function wrapEmailHtml(body: string): string {
		return `<!DOCTYPE html>
<html lang="de">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Email</title>
	<style>
		body {
			margin: 0;
			padding: 0;
			font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
			background-color: #f5f5f5;
		}
		.email-container {
			max-width: 600px;
			margin: 0 auto;
			background-color: #ffffff;
			padding: 40px 30px;
		}
		p { margin: 0.5rem 0; line-height: 1.6; }
		h1 { font-size: 2rem; font-weight: bold; margin: 1rem 0 0.5rem; }
		h2 { font-size: 1.5rem; font-weight: bold; margin: 1rem 0 0.5rem; }
		h3 { font-size: 1.25rem; font-weight: bold; margin: 1rem 0 0.5rem; }
		ul, ol { padding-left: 1.5rem; margin: 0.5rem 0; }
		li { margin: 0.25rem 0; }
		a { color: #3b82f6; text-decoration: underline; }
		img { max-width: 100%; height: auto; }
	</style>
</head>
<body>
	<div class="email-container">
		${body}
	</div>
</body>
</html>`;
	}
</script>

{#if loading}
	<div class="flex items-center justify-center py-12">
		<div class="skeleton w-32 h-32"></div>
	</div>
{:else if !template}
	<div class="space-y-6 animate-fade-in">
		<div class="panel">
			<div class="p-8 text-center">
				<p class="text-[var(--color-text-muted)]">Template nicht gefunden</p>
				<a href="/email/templates" class="text-[var(--color-accent)] hover:underline mt-4 inline-block">
					← Zurück zur Liste
				</a>
			</div>
		</div>
	</div>
{:else}
	<div class="space-y-6 animate-fade-in">
		<!-- Header -->
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold font-mono tracking-tight text-[var(--color-accent)]">
					TEMPLATE BEARBEITEN
				</h1>
				<p class="text-sm text-[var(--color-text-muted)] mt-1">
					{template.name}
				</p>
			</div>
			<div class="flex gap-2">
				<a
					href="/email/templates"
					class="px-3 py-1.5 text-xs font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded transition-all"
				>
					← ABBRECHEN
				</a>
			</div>
		</div>

		<div class="grid grid-cols-1 {showPreview ? 'lg:grid-cols-2' : ''} gap-4">
			<!-- Editor -->
			<div class="space-y-4">
				<div class="panel">
					<div class="panel-header">Template Details</div>
					<div class="p-4 space-y-4">
						<div>
							<label
								class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1"
							>
								Template Name *
							</label>
							<input
								type="text"
								bind:value={form.name}
								placeholder="z.B. Restaurant Cold Outreach"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
						</div>

						<div>
							<label
								class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1"
							>
								Betreff *
							</label>
							<input
								type="text"
								bind:value={form.subject}
								placeholder="Hallo {{ansprechpartner}}, digitale Lösungen für {{firma}}"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
							<p class="text-xs text-[var(--color-text-muted)] mt-1">
								Tipp: Nutze Platzhalter wie {`{{firma}}`} oder {`{{ansprechpartner}}`}
							</p>
						</div>
					</div>
				</div>

				<div class="panel">
					<div class="panel-header flex items-center justify-between">
						<span>Email Body</span>
						<button
							onclick={() => (showPreview = !showPreview)}
							class="text-xs font-mono text-[var(--color-accent)] hover:underline"
						>
							{showPreview ? 'VORSCHAU AUSBLENDEN' : 'VORSCHAU ANZEIGEN'}
						</button>
					</div>
					<div class="p-4">
						<EmailTemplateEditor
							bind:value={form.htmlBody}
							{placeholders}
						/>
					</div>
				</div>

				<div class="flex gap-2">
					<button
						onclick={saveTemplate}
						disabled={saving}
						class="px-4 py-2 text-sm font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded transition-all disabled:opacity-50 shadow-[0_0_12px_rgba(255,165,2,0.3)]"
					>
						{saving ? 'SPEICHERT...' : 'ÄNDERUNGEN SPEICHERN'}
					</button>
					<a
						href="/email/templates"
						class="px-4 py-2 text-sm font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] rounded transition-all inline-block"
					>
						ABBRECHEN
					</a>
				</div>
			</div>

			<!-- Preview -->
			{#if showPreview}
				<div class="space-y-4">
					<div class="panel">
						<div class="panel-header">Live Vorschau</div>
						<div class="p-4 space-y-3">
							<div>
								<div class="text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									Betreff:
								</div>
								<div class="text-sm text-[var(--color-text-primary)]">
									{renderPreview(form.subject || '(Kein Betreff)')}
								</div>
							</div>

							<div class="border-t border-[var(--color-surface-600)] pt-3">
								<div class="text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">
									Email Body:
								</div>
								<div class="bg-white rounded p-4 text-sm" style="color: #1f2937;">
									{@html renderPreview(form.htmlBody || '<p class="text-gray-400">Email Body erscheint hier...</p>')}
								</div>
							</div>

							<div class="border-t border-[var(--color-surface-600)] pt-3">
								<div class="text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">
									Beispieldaten:
								</div>
								<div class="text-xs text-[var(--color-text-muted)] space-y-0.5 font-mono">
									{#each Object.entries(exampleData).slice(0, 6) as [key, value]}
										<div>{key}: {value}</div>
									{/each}
									<div class="text-[10px] pt-1">... und weitere</div>
								</div>
							</div>
						</div>
					</div>

					<div class="panel">
						<div class="panel-header">Verfügbare Platzhalter</div>
						<div class="p-3 grid grid-cols-2 gap-1">
							{#each placeholders as placeholder}
								<div class="text-xs font-mono text-[var(--color-text-secondary)]">
									{`{{${placeholder}}}`}
								</div>
							{/each}
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>
{/if}
