<script lang="ts">
	import { onMount } from 'svelte';
	import { BRANCHEN_KATEGORIEN } from '$lib/types/lead';

	const CONVEX_URL = 'https://energetic-civet-402.convex.cloud';

	interface CoverageEntry {
		plz: string;
		ort: string;
		branche: string;
		kategorie: string;
		suchergebnisse: number;
		leadsGefunden: number;
		leadsGefiltert: number;
		gescraptAm: string;
	}

	interface CoverageStats {
		totalCombos: number;
		plzCount: number;
		branchenCount: number;
		totalSuchergebnisse: number;
		totalLeadsGefunden: number;
		totalLeadsGefiltert: number;
	}

	let data = $state<CoverageEntry[]>([]);
	let stats = $state<CoverageStats | null>(null);
	let loading = $state(true);
	let error = $state('');

	// Filters
	let filterPlz = $state('');
	let filterKategorie = $state('');

	// Tooltip
	let tooltip = $state<{ text: string; x: number; y: number } | null>(null);

	// All unique PLZs from data
	const allPlzs = $derived([...new Set(data.map(d => d.plz))].sort());

	// Filtered PLZs
	const plzs = $derived(
		filterPlz
			? allPlzs.filter(p => p.includes(filterPlz))
			: allPlzs
	);

	// Filtered categories
	const categories = $derived(
		filterKategorie
			? BRANCHEN_KATEGORIEN.filter(c => c.name === filterKategorie)
			: BRANCHEN_KATEGORIEN
	);

	// Total possible combos
	const totalBranchen = BRANCHEN_KATEGORIEN.reduce((s, c) => s + c.branchen.length, 0);
	const totalMoeglich = $derived(allPlzs.length * totalBranchen);

	// Lookup map: "branche|plz" -> entry
	const lookupMap = $derived.by(() => {
		const m = new Map<string, CoverageEntry>();
		for (const entry of data) {
			m.set(`${entry.branche}|${entry.plz}`, entry);
		}
		return m;
	});

	function getEntry(branche: string, plz: string): CoverageEntry | undefined {
		return lookupMap.get(`${branche}|${plz}`);
	}

	function getCellColor(entry: CoverageEntry | undefined): string {
		if (!entry) return 'bg-[var(--color-surface-700)]';
		if (entry.leadsGefunden === 0 && entry.suchergebnisse === 0) return 'bg-yellow-900/60';
		if (entry.leadsGefunden === 0) return 'bg-yellow-800/50';
		if (entry.leadsGefunden >= 10) return 'bg-emerald-500';
		if (entry.leadsGefunden >= 5) return 'bg-emerald-600';
		if (entry.leadsGefunden >= 2) return 'bg-emerald-700';
		return 'bg-emerald-800';
	}

	function getCategoryProgress(kategorie: string, branchen: string[]): { done: number; total: number } {
		let done = 0;
		const total = branchen.length * plzs.length;
		for (const b of branchen) {
			for (const p of plzs) {
				if (lookupMap.has(`${b}|${p}`)) done++;
			}
		}
		return { done, total };
	}

	function showTooltip(e: MouseEvent, branche: string, plz: string) {
		const entry = getEntry(branche, plz);
		if (entry) {
			const datum = new Date(entry.gescraptAm).toLocaleDateString('de-DE');
			tooltip = {
				text: `${branche} ${plz}: ${entry.suchergebnisse} Ergebnisse, ${entry.leadsGefunden} Leads, gescrapt am ${datum}`,
				x: e.clientX,
				y: e.clientY
			};
		} else {
			tooltip = {
				text: `${branche} ${plz}: noch nicht gescrapt`,
				x: e.clientX,
				y: e.clientY
			};
		}
	}

	function hideTooltip() {
		tooltip = null;
	}

	async function convexQuery(path: string, args: Record<string, unknown> = {}) {
		const res = await fetch(`${CONVEX_URL}/api/query`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ path, args })
		});
		if (!res.ok) throw new Error(`Convex query failed: ${res.status}`);
		const json = await res.json();
		return json.value;
	}

	let autoRefreshInterval: ReturnType<typeof setInterval>;
	let lastUpdate = $state('');

	async function loadData() {
		try {
			const [allData, statsData] = await Promise.all([
				convexQuery('coverage:getAll'),
				convexQuery('coverage:stats')
			]);
			data = allData;
			stats = statsData;
			lastUpdate = new Date().toLocaleTimeString('de-DE');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Unbekannter Fehler';
		} finally {
			loading = false;
		}
	}

	onMount(async () => {
		await loadData();
		autoRefreshInterval = setInterval(loadData, 30_000);
		return () => clearInterval(autoRefreshInterval);
	});

	// removed old onMount
</script>

<svelte:head>
	<title>Scraper Coverage — ManniLeads</title>
</svelte:head>

<!-- Tooltip -->
{#if tooltip}
	<div
		class="fixed z-[100] px-3 py-2 text-xs font-mono bg-[var(--color-surface-700)] border border-[var(--color-surface-500)] text-[var(--color-text-primary)] rounded-md shadow-lg pointer-events-none max-w-xs"
		style="left: {tooltip.x + 12}px; top: {tooltip.y - 8}px;"
	>
		{tooltip.text}
	</div>
{/if}

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<h1 class="text-xl font-bold text-[var(--color-text-primary)]">Scraper Coverage</h1>
		{#if !loading && data.length > 0}
			<div class="flex items-center gap-3">
				<span class="text-xs font-mono text-[var(--color-text-muted)]">{data.length} Einträge</span>
				{#if lastUpdate}
					<span class="text-xs font-mono text-[var(--color-text-muted)]">Aktualisiert {lastUpdate}</span>
				{/if}
				<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" title="Auto-Refresh alle 30s"></span>
			</div>
		{/if}
	</div>

	{#if loading}
		<div class="flex items-center gap-3 py-12 justify-center">
			<div class="w-5 h-5 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin"></div>
			<span class="text-sm text-[var(--color-text-muted)]">Lade Coverage-Daten...</span>
		</div>
	{:else if error}
		<div class="panel p-4 text-[var(--color-error)] text-sm font-mono">{error}</div>
	{:else}
		<!-- Stats Cards -->
		<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 stagger">
			<div class="panel p-3">
				<div class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Gescrapt</div>
				<div class="text-lg font-bold font-mono text-[var(--color-accent)]">{stats?.totalCombos ?? data.length}</div>
				<div class="text-[10px] text-[var(--color-text-muted)]">von {totalMoeglich} möglich</div>
			</div>
			<div class="panel p-3">
				<div class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">PLZ abgedeckt</div>
				<div class="text-lg font-bold font-mono text-[var(--color-text-primary)]">{stats?.plzCount ?? allPlzs.length}</div>
			</div>
			<div class="panel p-3">
				<div class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Branchen</div>
				<div class="text-lg font-bold font-mono text-[var(--color-text-primary)]">{stats?.branchenCount ?? new Set(data.map(d => d.branche)).size}</div>
				<div class="text-[10px] text-[var(--color-text-muted)]">von {totalBranchen}</div>
			</div>
			<div class="panel p-3">
				<div class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Suchergebnisse</div>
				<div class="text-lg font-bold font-mono text-[var(--color-info)]">{(stats?.totalSuchergebnisse ?? 0).toLocaleString('de-DE')}</div>
			</div>
			<div class="panel p-3">
				<div class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Leads gefunden</div>
				<div class="text-lg font-bold font-mono text-[var(--color-success)]">{(stats?.totalLeadsGefunden ?? 0).toLocaleString('de-DE')}</div>
			</div>
			<div class="panel p-3">
				<div class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Leads gefiltert</div>
				<div class="text-lg font-bold font-mono text-[var(--color-warning)]">{(stats?.totalLeadsGefiltert ?? 0).toLocaleString('de-DE')}</div>
			</div>
		</div>

		<!-- Filters -->
		<div class="flex flex-wrap gap-3 items-end">
			<div>
				<label class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] block mb-1">PLZ filtern</label>
				<input
					type="text"
					bind:value={filterPlz}
					placeholder="z.B. 19053"
					class="bg-[var(--color-surface-700)] border border-[var(--color-surface-500)] text-[var(--color-text-primary)] rounded-md px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] w-32"
				/>
			</div>
			<div>
				<label class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)] block mb-1">Kategorie</label>
				<select
					bind:value={filterKategorie}
					class="bg-[var(--color-surface-700)] border border-[var(--color-surface-500)] text-[var(--color-text-primary)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
				>
					<option value="">Alle Kategorien</option>
					{#each BRANCHEN_KATEGORIEN as cat}
						<option value={cat.name}>{cat.name}</option>
					{/each}
				</select>
			</div>
			{#if filterPlz || filterKategorie}
				<button
					onclick={() => { filterPlz = ''; filterKategorie = ''; }}
					class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-accent)] transition-colors cursor-pointer"
				>✕ Filter zurücksetzen</button>
			{/if}
		</div>

		<!-- Heatmap -->
		{#if plzs.length === 0}
			<div class="panel p-6 text-center text-sm text-[var(--color-text-muted)]">
				Keine Daten für die gewählten Filter.
			</div>
		{:else}
			<div class="panel overflow-x-auto">
				<!-- PLZ Header -->
				<div class="sticky top-0 z-10 bg-[var(--color-surface-800)] border-b border-[var(--color-surface-600)]">
					<div class="flex">
						<div class="w-48 min-w-48 shrink-0 px-3 py-2 text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Branche</div>
						{#each plzs as plz}
							<div class="w-8 min-w-8 shrink-0 text-center py-2">
								<span class="text-[8px] font-mono text-[var(--color-text-muted)] [writing-mode:vertical-lr] rotate-180">{plz}</span>
							</div>
						{/each}
					</div>
				</div>

				<!-- Category Groups -->
				{#each categories as cat}
					{@const progress = getCategoryProgress(cat.name, cat.branchen)}
					<!-- Category Header -->
					<div class="border-t border-[var(--color-surface-500)] bg-[var(--color-surface-800)]/80 px-3 py-2 flex items-center justify-between">
						<span class="text-xs font-bold text-[var(--color-accent)] uppercase tracking-wider">{cat.name}</span>
						<div class="flex items-center gap-2">
							<div class="w-24 h-1.5 bg-[var(--color-surface-600)] rounded-full overflow-hidden">
								<div
									class="h-full bg-[var(--color-accent)] rounded-full transition-all"
									style="width: {progress.total > 0 ? (progress.done / progress.total * 100) : 0}%"
								></div>
							</div>
							<span class="text-[10px] font-mono text-[var(--color-text-muted)]">{progress.done}/{progress.total}</span>
						</div>
					</div>

					<!-- Branchen Rows -->
					{#each cat.branchen as branche}
						<div class="flex hover:bg-[var(--color-surface-700)]/30 transition-colors">
							<div class="w-48 min-w-48 shrink-0 px-3 py-0.5 text-[11px] text-[var(--color-text-secondary)] truncate flex items-center">{branche}</div>
							{#each plzs as plz}
								{@const entry = getEntry(branche, plz)}
								<div
									class="w-8 min-w-8 shrink-0 flex items-center justify-center p-0.5"
									onmouseenter={(e) => showTooltip(e, branche, plz)}
									onmouseleave={hideTooltip}
								>
									<div class="w-5 h-5 rounded-sm {getCellColor(entry)} transition-colors"></div>
								</div>
							{/each}
						</div>
					{/each}
				{/each}
			</div>

			<!-- Legend -->
			<div class="flex flex-wrap items-center gap-4 text-[10px] text-[var(--color-text-muted)]">
				<span class="uppercase tracking-wider font-bold">Legende:</span>
				<span class="flex items-center gap-1.5"><span class="w-4 h-4 rounded-sm bg-[var(--color-surface-700)] inline-block"></span> Nicht gescrapt</span>
				<span class="flex items-center gap-1.5"><span class="w-4 h-4 rounded-sm bg-yellow-900/60 inline-block"></span> 0 Ergebnisse</span>
				<span class="flex items-center gap-1.5"><span class="w-4 h-4 rounded-sm bg-emerald-800 inline-block"></span> 1 Lead</span>
				<span class="flex items-center gap-1.5"><span class="w-4 h-4 rounded-sm bg-emerald-600 inline-block"></span> 5+ Leads</span>
				<span class="flex items-center gap-1.5"><span class="w-4 h-4 rounded-sm bg-emerald-500 inline-block"></span> 10+ Leads</span>
			</div>
		{/if}
	{/if}
</div>
