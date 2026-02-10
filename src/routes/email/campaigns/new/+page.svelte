<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { ConvexHttpClient } from 'convex/browser';
	import { PUBLIC_CONVEX_URL } from '$env/static/public';
	import { api } from '$lib/convex/_generated/api';

	const client = new ConvexHttpClient(PUBLIC_CONVEX_URL);

	let accounts = $state<any[]>([]);
	let templates = $state<any[]>([]);
	let leads = $state<any[]>([]);
	let loading = $state(true);

	// Form state
	let form = $state({
		name: '',
		templateId: '',
		accountId: '',
		filters: {
			branche: '',
			plz: '',
			segment: '',
			status: '',
			scoreMin: 0,
			scoreMax: 100
		}
	});

	// Filtered leads preview
	let filteredLeads = $derived(
		leads.filter((lead: any) => {
			if (!lead.email || lead.email.trim() === '') return false;
			if (form.filters.branche && lead.branche !== form.filters.branche) return false;
			if (form.filters.plz && lead.plz !== form.filters.plz) return false;
			if (form.filters.segment && lead.segment !== form.filters.segment) return false;
			if (form.filters.status && lead.status !== form.filters.status) return false;
			if (lead.score < form.filters.scoreMin || lead.score > form.filters.scoreMax) return false;
			return true;
		})
	);

	// Unique values for filters
	let uniqueBranchen = $derived([...new Set(leads.map((l: any) => l.branche))].filter(Boolean));
	let uniquePLZ = $derived([...new Set(leads.map((l: any) => l.plz))].filter(Boolean));

	onMount(async () => {
		try {
			[accounts, templates, leads] = await Promise.all([
				client.query(api.email.listAccounts),
				client.query(api.email.listTemplates),
				client.query(api.leads.list)
			]);
		} catch (error) {
			console.error('Failed to load data:', error);
		} finally {
			loading = false;
		}
	});

	async function createCampaign() {
		try {
			const campaignId = await client.mutation(api.email.createCampaign, {
				name: form.name,
				templateId: form.templateId as any,
				accountId: form.accountId as any,
				filtersJson: JSON.stringify(form.filters)
			});
			await goto(`/email/campaigns/${campaignId}`);
		} catch (error) {
			console.error('Failed to create campaign:', error);
			alert('Fehler beim Erstellen: ' + error);
		}
	}
</script>

<div class="space-y-6 animate-fade-in">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold font-mono tracking-tight text-[var(--color-accent)]">
				NEUE KAMPAGNE
			</h1>
			<p class="text-sm text-[var(--color-text-muted)] mt-1">Email-Kampagne konfigurieren & starten</p>
		</div>
		<a
			href="/email"
			class="px-3 py-1.5 text-xs font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded transition-all"
		>
			← ZURÜCK
		</a>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="skeleton w-32 h-32"></div>
		</div>
	{:else}
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
			<!-- Form -->
			<div class="lg:col-span-2 space-y-4">
				<!-- Basic Settings -->
				<div class="panel">
					<div class="panel-header">Kampagnen-Einstellungen</div>
					<div class="p-4 space-y-4">
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								Kampagnen-Name
							</label>
							<input
								type="text"
								bind:value={form.name}
								placeholder="z.B. Restaurant Cold Outreach Q1 2026"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
						</div>

						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div>
								<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									Template
								</label>
								<select
									bind:value={form.templateId}
									class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
								>
									<option value="">— Template wählen —</option>
									{#each templates as template}
										<option value={template._id}>{template.name}</option>
									{/each}
								</select>
							</div>

							<div>
								<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									Email Account
								</label>
								<select
									bind:value={form.accountId}
									class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
								>
									<option value="">— Account wählen —</option>
									{#each accounts.filter((a) => a.active) as account}
										<option value={account._id}>{account.name} ({account.fromEmail})</option>
									{/each}
								</select>
							</div>
						</div>
					</div>
				</div>

				<!-- Targeting / Filters -->
				<div class="panel">
					<div class="panel-header">Lead-Targeting</div>
					<div class="p-4 space-y-4">
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div>
								<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									Branche
								</label>
								<select
									bind:value={form.filters.branche}
									class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
								>
									<option value="">— Alle —</option>
									{#each uniqueBranchen as branche}
										<option value={branche}>{branche}</option>
									{/each}
								</select>
							</div>

							<div>
								<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									PLZ
								</label>
								<select
									bind:value={form.filters.plz}
									class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
								>
									<option value="">— Alle —</option>
									{#each uniquePLZ as plz}
										<option value={plz}>{plz}</option>
									{/each}
								</select>
							</div>

							<div>
								<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									Segment
								</label>
								<select
									bind:value={form.filters.segment}
									class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
								>
									<option value="">— Alle —</option>
									<option value="HOT">HOT</option>
									<option value="WARM">WARM</option>
									<option value="COLD">COLD</option>
									<option value="DISQUALIFIED">DISQUALIFIED</option>
								</select>
							</div>

							<div>
								<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									Status
								</label>
								<select
									bind:value={form.filters.status}
									class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
								>
									<option value="">— Alle —</option>
									<option value="Neu">Neu</option>
									<option value="Kontaktiert">Kontaktiert</option>
									<option value="Interessiert">Interessiert</option>
									<option value="Angebot">Angebot</option>
									<option value="Gewonnen">Gewonnen</option>
									<option value="Verloren">Verloren</option>
								</select>
							</div>
						</div>

						<div class="grid grid-cols-2 gap-4">
							<div>
								<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									Min Score: {form.filters.scoreMin}
								</label>
								<input
									type="range"
									bind:value={form.filters.scoreMin}
									min="0"
									max="100"
									step="5"
									class="w-full"
								/>
							</div>
							<div>
								<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									Max Score: {form.filters.scoreMax}
								</label>
								<input
									type="range"
									bind:value={form.filters.scoreMax}
									min="0"
									max="100"
									step="5"
									class="w-full"
								/>
							</div>
						</div>
					</div>
				</div>

				<!-- Submit -->
				<div class="flex gap-2">
					<button
						onclick={createCampaign}
						disabled={!form.name || !form.templateId || !form.accountId}
						class="px-4 py-2 text-sm font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed text-[var(--color-surface-900)] rounded transition-all shadow-[0_0_12px_rgba(255,165,2,0.3)]"
					>
						KAMPAGNE ERSTELLEN
					</button>
					<a
						href="/email"
						class="px-4 py-2 text-sm font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] rounded transition-all"
					>
						ABBRECHEN
					</a>
				</div>
			</div>

			<!-- Preview Sidebar -->
			<div class="panel">
				<div class="panel-header">Ziel-Leads</div>
				<div class="p-3 space-y-3">
					<div class="text-center py-4">
						<div class="text-4xl font-mono font-bold text-[var(--color-accent)]">
							{filteredLeads.length}
						</div>
						<div class="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-widest mt-1">
							Empfänger
						</div>
					</div>

					{#if filteredLeads.length > 0}
						<div class="space-y-2 max-h-96 overflow-y-auto">
							{#each filteredLeads.slice(0, 10) as lead}
								<div class="p-2 bg-[var(--color-surface-700)] rounded text-xs">
									<div class="font-medium text-[var(--color-text-primary)]">{lead.firma}</div>
									<div class="text-[var(--color-text-muted)]">{lead.email}</div>
								</div>
							{/each}
							{#if filteredLeads.length > 10}
								<div class="text-center text-xs text-[var(--color-text-muted)] pt-2">
									+ {filteredLeads.length - 10} weitere
								</div>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>
