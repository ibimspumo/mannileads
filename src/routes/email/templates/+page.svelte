<script lang="ts">
	import { onMount } from 'svelte';
	
	
	import { convex, api } from '$lib/convex';

	

	let templates = $state<any[]>([]);
	let loading = $state(true);

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
			<a
				href="/email/templates/new"
				class="px-3 py-1.5 text-xs font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded transition-all shadow-[0_0_12px_rgba(255,165,2,0.3)]"
			>
				+ NEUES TEMPLATE
			</a>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="skeleton w-32 h-32"></div>
		</div>
	{:else}
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
									<a
										href="/email/templates/{template._id}"
										class="px-2 py-1 text-xs font-mono text-[var(--color-accent)] hover:underline"
									>
										BEARBEITEN
									</a>
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
