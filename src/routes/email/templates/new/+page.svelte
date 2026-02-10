<script lang="ts">
	import { goto } from '$app/navigation';
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

	// Form state
	let form = $state({
		name: '',
		subject: '',
		htmlBody: ''
	});

	let saving = $state(false);
	let showPreview = $state(false);

	// Render template with example data
	function renderPreview(template: string): string {
		let rendered = template;
		for (const [key, value] of Object.entries(exampleData)) {
			const regex = new RegExp(`{{${key}}}`, 'g');
			rendered = rendered.replace(regex, value);
		}
		return rendered;
	}

	$effect(() => {
		// Auto-update preview when body changes
		if (form.htmlBody) {
			// Debounce would be nice here but let's keep it simple
		}
	});

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

			await convex.mutation(api.email.createTemplate, {
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

<div class="space-y-6 animate-fade-in">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold font-mono tracking-tight text-[var(--color-accent)]">
				NEUES EMAIL TEMPLATE
			</h1>
			<p class="text-sm text-[var(--color-text-muted)] mt-1">
				Erstelle ein neues Template mit WYSIWYG Editor
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
					{saving ? 'SPEICHERT...' : 'TEMPLATE ERSTELLEN'}
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
