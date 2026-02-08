<script lang="ts">
	import { leads } from '$lib/stores/leads';
	import { filters } from '$lib/stores/filters';
	import { searchLeads } from '$lib/utils/search';
	import { exportCSV, exportJSON, downloadFile } from '$lib/utils/export';
	import FilterBar from '$lib/components/molecules/FilterBar.svelte';
	import LeadTable from '$lib/components/organisms/LeadTable.svelte';
	import Button from '$lib/components/atoms/Button.svelte';
	import type { Lead } from '$lib/types/lead';

	const loading = $derived($leads.length === 0 && !leads.loaded);

	const filtered = $derived.by(() => {
		let result = $leads;
		if ($filters.search) result = searchLeads(result, $filters.search);
		if ($filters.segment) result = result.filter(l => l.segment === $filters.segment);
		if ($filters.status) result = result.filter(l => l.status === $filters.status);
		if ($filters.plz) result = result.filter(l => l.plz.startsWith($filters.plz));
		result = result.filter(l => l.score >= $filters.scoreMin && l.score <= $filters.scoreMax);
		const dir = $filters.sortDir === 'asc' ? 1 : -1;
		const key = $filters.sortBy as keyof Lead;
		result = [...result].sort((a, b) => {
			const va = a[key] ?? '';
			const vb = b[key] ?? '';
			if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir;
			return String(va).localeCompare(String(vb)) * dir;
		});
		return result;
	});

	function toggleSort(col: string) {
		filters.update(f => ({
			...f,
			sortBy: col,
			sortDir: f.sortBy === col && f.sortDir === 'desc' ? 'asc' : 'desc'
		}));
	}

	function doExportCSV() {
		downloadFile(exportCSV(filtered), `leads-export-${new Date().toISOString().slice(0,10)}.csv`, 'text/csv');
	}

	function doExportJSON() {
		downloadFile(exportJSON(filtered), `leads-export-${new Date().toISOString().slice(0,10)}.json`, 'application/json');
	}
</script>

<svelte:head>
	<title>Leads — ManniLeads</title>
</svelte:head>

<div class="space-y-4 animate-fade-in">
	<div class="flex items-center justify-between flex-wrap gap-3">
		<h1 class="text-xl font-bold text-[var(--color-text-primary)]">
			Leads <span class="text-sm font-normal text-[var(--color-text-muted)] font-mono">({filtered.length})</span>
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
			<LeadTable filteredLeads={filtered} sortBy={$filters.sortBy} sortDir={$filters.sortDir} onsort={toggleSort} />
		</div>
	{/if}
</div>
