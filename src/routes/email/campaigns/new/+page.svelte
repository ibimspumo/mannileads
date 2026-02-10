<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { convex, api } from '$lib/convex';
	import SearchableDropdown from '$lib/components/SearchableDropdown.svelte';
	import EmailPreviewModal from '$lib/components/EmailPreviewModal.svelte';

	let accounts = $state<any[]>([]);
	let templates = $state<any[]>([]);
	let leadCount = $state(0);
	let leadPreview = $state<any[]>([]);
	let loading = $state(true);
	let countingLeads = $state(false);

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

	// Unique filter values (loaded dynamically)
	let uniqueBranchen = $state<string[]>([]);
	let uniquePLZ = $state<string[]>([]);

	// Email preview modal state
	let showPreview = $state(false);
	let previewData = $state<any>(null);
	let previewLoading = $state(false);

	async function loadLeadCount() {
		countingLeads = true;
		try {
			const result = await convex.action(api.email.countLeadsForCampaign, {
				branche: form.filters.branche || undefined,
				plz: form.filters.plz || undefined,
				segment: form.filters.segment || undefined,
				status: form.filters.status || undefined,
				scoreMin: form.filters.scoreMin,
				scoreMax: form.filters.scoreMax,
			});
			leadCount = result.count;
			leadPreview = result.preview;
		} catch (error) {
			console.error('Failed to count leads:', error);
		} finally {
			countingLeads = false;
		}
	}

	// Debounced filter change handler
	let filterTimeout: any;
	function onFilterChange() {
		clearTimeout(filterTimeout);
		filterTimeout = setTimeout(loadLeadCount, 300);
	}

	async function openPreview(lead: any) {
		if (!form.templateId || !form.accountId) return;
		previewLoading = true;
		showPreview = true;
		try {
			const data = await convex.query(api.email.previewEmailWithSignature, {
				templateId: form.templateId as any,
				accountId: form.accountId as any,
				leadId: lead._id,
			});
			previewData = data;
		} catch (error) {
			console.error('Preview failed:', error);
			previewData = null;
		} finally {
			previewLoading = false;
		}
	}

	onMount(async () => {
		try {
			const [acc, tmpl] = await Promise.all([
				convex.query(api.email.listAccounts),
				convex.query(api.email.listTemplates),
			]);
			accounts = acc;
			templates = tmpl;
			// Load filter options dynamically from leads table
			convex.action(api.email.getFilterOptions).then((opts: any) => {
				uniqueBranchen = opts.branchen;
				uniquePLZ = opts.plz;
			}).catch((e: any) => console.error('Filter options failed:', e));
			await loadLeadCount();
		} catch (error) {
			console.error('Failed to load data:', error);
		} finally {
			loading = false;
		}
	});

	async function createCampaign() {
		try {
			const campaignId = await convex.mutation(api.email.createCampaign, {
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
							<SearchableDropdown
								options={uniqueBranchen}
								bind:value={form.filters.branche}
								label="Branche"
								placeholder="— Alle Branchen —"
								onchange={onFilterChange}
							/>

							<SearchableDropdown
								options={uniquePLZ}
								bind:value={form.filters.plz}
								label="PLZ"
								placeholder="— Alle PLZ —"
								onchange={onFilterChange}
							/>

							<div>
								<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
									Segment
								</label>
								<select
									bind:value={form.filters.segment} onchange={onFilterChange}
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
									bind:value={form.filters.status} onchange={onFilterChange}
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
									bind:value={form.filters.scoreMin} oninput={onFilterChange}
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
									bind:value={form.filters.scoreMax} oninput={onFilterChange}
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
						{#if countingLeads}
							<div class="text-sm font-mono text-[var(--color-text-muted)] animate-pulse">Zähle...</div>
						{:else}
							<div class="text-4xl font-mono font-bold text-[var(--color-accent)]">
								{leadCount.toLocaleString('de-DE')}
							</div>
						{/if}
						<div class="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-widest mt-1">
							Empfänger
						</div>
					</div>

					{#if leadPreview.length > 0}
						<div class="space-y-2 max-h-96 overflow-y-auto">
							{#each leadPreview as lead}
								<button
									type="button"
									onclick={() => openPreview(lead)}
									disabled={!form.templateId || !form.accountId}
									class="w-full text-left p-2 bg-[var(--color-surface-700)] rounded text-xs hover:bg-[var(--color-surface-600)] transition-colors cursor-pointer disabled:cursor-default disabled:opacity-60 group"
								>
									<div class="font-medium text-[var(--color-text-primary)] group-hover:text-[var(--color-accent)] transition-colors">{lead.firma}</div>
									<div class="text-[var(--color-text-muted)]">{lead.email}</div>
									{#if form.templateId && form.accountId}
										<div class="text-[10px] text-[var(--color-accent)] opacity-0 group-hover:opacity-100 transition-opacity mt-0.5">
											▶ Preview anzeigen
										</div>
									{/if}
								</button>
							{/each}
							{#if leadCount > 10}
								<div class="text-center text-xs text-[var(--color-text-muted)] pt-2">
									+ {(leadCount - 10).toLocaleString('de-DE')} weitere
								</div>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
</div>

<!-- Email Preview Modal -->
{#if previewData}
	<EmailPreviewModal
		bind:show={showPreview}
		subject={previewData.subject}
		htmlBody={previewData.htmlBody}
		fromName={previewData.account.fromName}
		fromEmail={previewData.account.fromEmail}
		toFirma={previewData.lead.firma}
		toEmail={previewData.lead.email}
	/>
{:else if showPreview}
	<EmailPreviewModal
		bind:show={showPreview}
		subject="Laden..."
		htmlBody="<p>Lade Preview...</p>"
		fromName=""
		fromEmail=""
		toFirma=""
		toEmail=""
	/>
{/if}
