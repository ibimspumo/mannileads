<script lang="ts">
	import Select from '$lib/components/atoms/Select.svelte';
	import SearchInput from './SearchInput.svelte';
	import { filters } from '$lib/stores/filters';
	import { SEGMENTS, STATUSES } from '$lib/types/lead';

	const segmentOptions = [{ value: '', label: 'Alle Segmente' }, ...SEGMENTS.map(s => ({ value: s, label: s }))];
	const statusOptions = [{ value: '', label: 'Alle Status' }, ...STATUSES.map(s => ({ value: s, label: s }))];
</script>

<div class="flex flex-wrap items-end gap-3">
	<div class="flex-1 min-w-[200px]">
		<SearchInput bind:value={$filters.search} placeholder="Firma, Ort, Branche suchen..." />
	</div>
	<div class="w-40">
		<Select options={segmentOptions} bind:value={$filters.segment} />
	</div>
	<div class="w-40">
		<Select options={statusOptions} bind:value={$filters.status} />
	</div>
	<div class="w-28">
		<input type="text" placeholder="PLZ" bind:value={$filters.plz}
			class="w-full bg-[var(--color-surface-700)] border border-[var(--color-surface-500)] text-[var(--color-text-primary)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] placeholder:text-[var(--color-text-muted)]"
		/>
	</div>
</div>
