<script lang="ts">
	import { onMount } from 'svelte';
	
	
	import { convex, api } from '$lib/convex';

	

	let templates = $state<any[]>([]);
	let loading = $state(true);
	let showForm = $state(false);
	let editingId = $state<string | null>(null);

	// Available placeholders from Lead schema
	const placeholders = [
		'firma',
		'website',
		'branche',
		'groesse',
		'plz',
		'ort',
		'ansprechpartner',
		'position',
		'email',
		'telefon'
	];

	// Form state
	let form = $state({
		name: '',
		subject: '',
		htmlBody: ''
	});

	onMount(async () => {
		await loadTemplates();
	});

	async function loadTemplates() {
		try {
			templates = await convex.query(api.email.listTemplates);
		} catch (error) {
			console.error('Failed to load templates:', error);
		} finally {
			loading = false;
		}
	}

	function resetForm() {
		form = {
			name: '',
			subject: '',
			htmlBody: ''
		};
		editingId = null;
		showForm = false;
	}

	function editTemplate(template: any) {
		form = {
			name: template.name,
			subject: template.subject,
			htmlBody: template.htmlBody
		};
		editingId = template._id;
		showForm = true;
	}

	async function saveTemplate() {
		try {
			// Extract placeholders used in template
			const usedPlaceholders = placeholders.filter(
				(p) => form.subject.includes(`{{${p}}}`) || form.htmlBody.includes(`{{${p}}}`)
			);

			if (editingId) {
				await convex.mutation(api.email.updateTemplate, {
					id: editingId as any,
					...form,
					placeholders: usedPlaceholders
				});
			} else {
				await convex.mutation(api.email.createTemplate, {
					...form,
					placeholders: usedPlaceholders
				});
			}
			await loadTemplates();
			resetForm();
		} catch (error) {
			console.error('Failed to save template:', error);
			alert('Fehler beim Speichern: ' + error);
		}
	}

	async function deleteTemplate(id: string) {
		if (!confirm('Template wirklich löschen?')) return;
		try {
			await convex.mutation(api.email.deleteTemplate, { id: id as any });
			await loadTemplates();
		} catch (error) {
			console.error('Failed to delete template:', error);
			alert('Fehler beim Löschen: ' + error);
		}
	}

	function insertPlaceholder(placeholder: string) {
		// Insert at cursor position in htmlBody textarea
		const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
		if (!textarea) return;

		const start = textarea.selectionStart;
		const end = textarea.selectionEnd;
		const text = form.htmlBody;
		const before = text.substring(0, start);
		const after = text.substring(end);

		form.htmlBody = before + `{{${placeholder}}}` + after;

		// Move cursor after inserted placeholder
		setTimeout(() => {
			textarea.focus();
			textarea.setSelectionRange(start + placeholder.length + 4, start + placeholder.length + 4);
		}, 0);
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleDateString('de-DE', {
			day: '2-digit',
			month: '2-digit',
			year: 'numeric'
		});
	}
</script>

<div class="space-y-6 animate-fade-in">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold font-mono tracking-tight text-[var(--color-accent)]">
				EMAIL TEMPLATES
			</h1>
			<p class="text-sm text-[var(--color-text-muted)] mt-1">Campaign Email Templates mit Platzhaltern</p>
		</div>
		<div class="flex gap-2">
			<a
				href="/email"
				class="px-3 py-1.5 text-xs font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded transition-all"
			>
				← ZURÜCK
			</a>
			<button
				onclick={() => (showForm = !showForm)}
				class="px-3 py-1.5 text-xs font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded transition-all shadow-[0_0_12px_rgba(255,165,2,0.3)]"
			>
				{showForm ? 'ABBRECHEN' : '+ NEUES TEMPLATE'}
			</button>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="skeleton w-32 h-32"></div>
		</div>
	{:else}
		<!-- Form -->
		{#if showForm}
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-4 animate-fade-in">
				<!-- Editor -->
				<div class="lg:col-span-2 panel">
					<div class="panel-header">{editingId ? 'Template bearbeiten' : 'Neues Template'}</div>
					<div class="p-4 space-y-4">
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								Template Name
							</label>
							<input
								type="text"
								bind:value={form.name}
								placeholder="z.B. Restaurant Cold Outreach"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
						</div>

						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								Betreff
							</label>
							<input
								type="text"
								bind:value={form.subject}
								placeholder="Hallo {{ansprechpartner}}, Digitalisierung für {{firma}}"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
						</div>

						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								HTML Body
							</label>
							<textarea
								bind:value={form.htmlBody}
								rows="16"
								placeholder="<p>Hallo {{ansprechpartner}},</p>..."
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] font-mono focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							></textarea>
						</div>

						<div class="flex gap-2 pt-2">
							<button
								onclick={saveTemplate}
								class="px-4 py-2 text-sm font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded transition-all"
							>
								{editingId ? 'AKTUALISIEREN' : 'ERSTELLEN'}
							</button>
							<button
								onclick={resetForm}
								class="px-4 py-2 text-sm font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] rounded transition-all"
							>
								ABBRECHEN
							</button>
						</div>
					</div>
				</div>

				<!-- Placeholders Sidebar -->
				<div class="panel">
					<div class="panel-header">Platzhalter</div>
					<div class="p-3 space-y-2">
						<p class="text-xs text-[var(--color-text-muted)] mb-3">
							Klicke um in Body einzufügen:
						</p>
						{#each placeholders as placeholder}
							<button
								onclick={() => insertPlaceholder(placeholder)}
								class="w-full px-2 py-1.5 text-left text-xs font-mono bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] hover:text-[var(--color-accent)] text-[var(--color-text-secondary)] rounded transition-colors"
							>
								{`{{${placeholder}}}`}
							</button>
						{/each}
					</div>
				</div>
			</div>
		{/if}

		<!-- Templates List -->
		<div class="panel">
			<div class="panel-header">Templates</div>
			<div class="divide-y divide-[var(--color-surface-700)]">
				{#if templates.length === 0}
					<div class="p-8 text-center">
						<p class="text-sm text-[var(--color-text-muted)]">Keine Templates vorhanden.</p>
					</div>
				{:else}
					{#each templates as template}
						<div class="p-4 hover:bg-[var(--color-surface-700)] transition-colors">
							<div class="flex items-start justify-between">
								<div class="flex-1">
									<h3 class="font-bold text-[var(--color-text-primary)] mb-1">{template.name}</h3>
									<div class="text-sm text-[var(--color-text-secondary)] space-y-1">
										<div class="flex items-center gap-2">
											<span class="text-xs text-[var(--color-text-muted)]">Betreff:</span>
											<span class="font-mono text-xs">{template.subject}</span>
										</div>
										<div class="flex flex-wrap gap-1 mt-2">
											{#each template.placeholders as ph}
												<span
													class="inline-block px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider rounded bg-[var(--color-surface-600)] text-[var(--color-accent)]"
												>
													{`{{${ph}}}`}
												</span>
											{/each}
										</div>
										<div class="text-xs text-[var(--color-text-muted)] mt-2">
											Erstellt: {formatDate(template.createdAt)}
										</div>
									</div>
								</div>
								<div class="flex gap-1">
									<button
										onclick={() => editTemplate(template)}
										class="px-2 py-1 text-xs font-mono text-[var(--color-accent)] hover:underline"
									>
										BEARBEITEN
									</button>
									<button
										onclick={() => deleteTemplate(template._id)}
										class="px-2 py-1 text-xs font-mono text-[var(--color-error)] hover:underline"
									>
										LÖSCHEN
									</button>
								</div>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>
	{/if}
</div>
