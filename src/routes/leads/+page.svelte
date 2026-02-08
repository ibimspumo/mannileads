<script lang="ts">
	import { leads } from '$lib/stores/leads';
	import { filters } from '$lib/stores/filters';
	import { searchLeads } from '$lib/utils/search';
	import { exportCSV, exportJSON, downloadFile } from '$lib/utils/export';
	import FilterBar from '$lib/components/molecules/FilterBar.svelte';
	import LeadTable from '$lib/components/organisms/LeadTable.svelte';
	import Button from '$lib/components/atoms/Button.svelte';
	import type { Lead } from '$lib/types/lead';

	const filtered = $derived.by(() => {
		let result = $leads;
		// Search
		if ($filters.search) result = searchLeads(result, $filters.search);
		// Segment
		if ($filters.segment) result = result.filter(l => l.segment === $filters.segment);
		// Status
		if ($filters.status) result = result.filter(l => l.status === $filters.status);
		// PLZ
		if ($filters.plz) result = result.filter(l => l.plz.startsWith($filters.plz));
		// Score range
		result = result.filter(l => l.score >= $filters.scoreMin && l.score <= $filters.scoreMax);
		// Sort
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

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<h1 class="text-xl font-bold text-[var(--color-text-primary)]">
			Leads <span class="text-sm font-normal text-[var(--color-text-muted)]">({filtered.length})</span>
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

	<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg overflow-hidden">
		<LeadTable filteredLeads={filtered} sortBy={$filters.sortBy} sortDir={$filters.sortDir} onsort={toggleSort} />
	</div>
</div>
