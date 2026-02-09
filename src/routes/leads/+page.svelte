<script lang="ts">
	import { filters } from '$lib/stores/filters';
	import { exportCSV, exportJSON, downloadFile } from '$lib/utils/export';
	import FilterBar from '$lib/components/molecules/FilterBar.svelte';
	import LeadTable from '$lib/components/organisms/LeadTable.svelte';
	import Button from '$lib/components/atoms/Button.svelte';
	import type { Lead } from '$lib/types/lead';
	import { convex, api } from '$lib/convex';

	let currentPage = $state(1);
	let pageSize = 100;
	let loading = $state(true);
	let leads: Lead[] = $state([]);
	let total = $state(0);
	let totalPages = $state(1);

	// Debounce search
	let searchTimeout: ReturnType<typeof setTimeout>;
	let lastQuery = $state('');

	// Reactive fetch when filters or page change
	$effect(() => {
		const f = $filters;
		// Access all reactive deps
		const _page = currentPage;
		const _search = f.search;
		const _segment = f.segment;
		const _status = f.status;
		const _plz = f.plz;
		const _scoreMin = f.scoreMin;
		const _scoreMax = f.scoreMax;
		const _sortBy = f.sortBy;
		const _sortDir = f.sortDir;

		fetchLeads();
	});

	async function fetchLeads() {
		loading = true;
		try {
			const f = $filters;
			const result = await convex.action(api.leads.listPaginated, {
				page: currentPage,
				pageSize,
				segment: f.segment || undefined,
				branche: undefined,
				searchQuery: f.search || undefined,
				sortBy: f.sortBy,
				sortDir: f.sortDir,
				status: f.status || undefined,
				scoreMin: f.scoreMin,
				scoreMax: f.scoreMax,
				plz: f.plz || undefined,
			});
			leads = result.leads.map((d: any) => ({ ...d, id: d._id }));
			total = result.total;
			totalPages = result.totalPages;
		} catch (e) {
			console.error('Fetch error:', e);
		} finally {
			loading = false;
		}
	}

	// Reset to page 1 when filters change
	$effect(() => {
		const f = $filters;
		// Track filter values
		const key = `${f.search}|${f.segment}|${f.status}|${f.plz}|${f.scoreMin}|${f.scoreMax}`;
		if (key !== lastQuery) {
			lastQuery = key;
			currentPage = 1;
		}
	});

	function toggleSort(col: string) {
		filters.update(f => ({
			...f,
			sortBy: col,
			sortDir: f.sortBy === col && f.sortDir === 'desc' ? 'asc' : 'desc'
		}));
	}

	function goPage(p: number) {
		currentPage = Math.max(1, Math.min(p, totalPages));
	}

	function doExportCSV() {
		downloadFile(exportCSV(leads), `leads-export-${new Date().toISOString().slice(0,10)}.csv`, 'text/csv');
	}

	function doExportJSON() {
		downloadFile(exportJSON(leads), `leads-export-${new Date().toISOString().slice(0,10)}.json`, 'application/json');
	}

	// Page numbers to show
	const pageNumbers = $derived.by(() => {
		const pages: number[] = [];
		const start = Math.max(1, currentPage - 2);
		const end = Math.min(totalPages, currentPage + 2);
		for (let i = start; i <= end; i++) pages.push(i);
		return pages;
	});
</script>

<svelte:head>
	<title>Leads — ManniLeads</title>
</svelte:head>

<div class="space-y-4 animate-fade-in">
	<div class="flex items-center justify-between flex-wrap gap-3">
		<h1 class="text-xl font-bold text-[var(--color-text-primary)]">
			Leads <span class="text-sm font-normal text-[var(--color-text-muted)] font-mono">({total})</span>
		</h1>
		<div class="flex gap-2">
			<Button variant="ghost" size="sm" onclick={doExportCSV}>CSV ↓</Button>
			<Button variant="ghost" size="sm" onclick={doExportJSON}>JSON ↓</Button>
			<a href="/leads/new">
				<Button size="sm">+ Neuer Lead</Button>
			</a>
		</div>
	</div>

	<FilterBar />

	{#if loading}
		<div class="panel p-8">
			<div class="space-y-3">
				{#each [1,2,3,4,5] as _}
					<div class="flex gap-4">
						<div class="skeleton h-5 w-12"></div>
						<div class="skeleton h-5 w-40"></div>
						<div class="skeleton h-5 w-24"></div>
						<div class="skeleton h-5 w-20"></div>
						<div class="skeleton h-5 w-16"></div>
					</div>
				{/each}
			</div>
		</div>
	{:else}
		<div class="panel overflow-hidden">
			<LeadTable filteredLeads={leads} sortBy={$filters.sortBy} sortDir={$filters.sortDir} onsort={toggleSort} />
		</div>

		<!-- Paginierung -->
		{#if totalPages > 1}
			<div class="flex items-center justify-between px-1">
				<span class="text-xs text-[var(--color-text-muted)] font-mono">
					{(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, total)} von {total}
				</span>
				<div class="flex items-center gap-1">
					<button
						onclick={() => goPage(1)}
						disabled={currentPage === 1}
						class="px-2 py-1.5 text-xs font-mono rounded bg-[var(--color-surface-700)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-600)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
					>««</button>
					<button
						onclick={() => goPage(currentPage - 1)}
						disabled={currentPage === 1}
						class="px-2.5 py-1.5 text-xs font-mono rounded bg-[var(--color-surface-700)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-600)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
					>‹</button>
					{#each pageNumbers as p}
						<button
							onclick={() => goPage(p)}
							class="px-2.5 py-1.5 text-xs font-mono rounded transition-colors {p === currentPage ? 'bg-[var(--color-accent)] text-black font-bold' : 'bg-[var(--color-surface-700)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-600)]'}"
						>{p}</button>
					{/each}
					<button
						onclick={() => goPage(currentPage + 1)}
						disabled={currentPage === totalPages}
						class="px-2.5 py-1.5 text-xs font-mono rounded bg-[var(--color-surface-700)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-600)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
					>›</button>
					<button
						onclick={() => goPage(totalPages)}
						disabled={currentPage === totalPages}
						class="px-2 py-1.5 text-xs font-mono rounded bg-[var(--color-surface-700)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-600)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
					>»»</button>
				</div>
			</div>
		{/if}
	{/if}
</div>
