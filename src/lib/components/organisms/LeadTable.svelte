<script lang="ts">
	import type { Lead, Segment, LeadStatus } from '$lib/types/lead';
	import { SEGMENTS, STATUSES } from '$lib/types/lead';
	import ScoreBadge from '$lib/components/atoms/ScoreBadge.svelte';
	import Badge from '$lib/components/atoms/Badge.svelte';
	import { getSegmentColor } from '$lib/utils/scoring';
	import { leads } from '$lib/stores/leads';

	interface Props {
		filteredLeads: Lead[];
		sortBy: string;
		sortDir: 'asc' | 'desc';
		onsort?: (col: string) => void;
	}
	let { filteredLeads, sortBy, sortDir, onsort }: Props = $props();

	function sort(col: string) {
		onsort?.(col);
	}

	function updateStatus(lead: Lead, status: LeadStatus) {
		leads.update_lead(lead.id, { status }, `Status geändert: ${status}`);
	}

	function updateSegment(lead: Lead, segment: Segment) {
		leads.update_lead(lead.id, { segment, segmentManuell: true }, `Segment manuell: ${segment}`);
	}

	function sortIcon(col: string): string {
		if (sortBy !== col) return '⇅';
		return sortDir === 'asc' ? '↑' : '↓';
	}

	const columns = [
		{ key: 'score', label: 'Score', w: 'w-16' },
		{ key: 'firma', label: 'Firma', w: 'min-w-[160px]' },
		{ key: 'branche', label: 'Branche', w: 'w-28' },
		{ key: 'ort', label: 'Ort', w: 'w-28' },
		{ key: 'segment', label: 'Segment', w: 'w-32' },
		{ key: 'status', label: 'Status', w: 'w-36' },
		{ key: 'ansprechpartner', label: 'Kontakt', w: 'w-32' }
	];
</script>

<div class="overflow-x-auto">
	<table class="w-full text-sm">
		<thead>
			<tr class="border-b border-[var(--color-surface-600)]">
				{#each columns as col}
					<th class="{col.w} text-left px-3 py-2 text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider cursor-pointer hover:text-[var(--color-text-primary)] select-none"
						onclick={() => sort(col.key)}>
						{col.label} <span class="text-[10px] opacity-60">{sortIcon(col.key)}</span>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each filteredLeads as lead (lead.id)}
				<tr class="border-b border-[var(--color-surface-700)] hover:bg-[var(--color-surface-800)] transition-colors">
					<td class="px-3 py-2"><ScoreBadge score={lead.score} /></td>
					<td class="px-3 py-2">
						<a href="/leads/{lead.id}" class="text-[var(--color-text-primary)] hover:text-[var(--color-accent)] font-medium">
							{lead.firma || '(Ohne Name)'}
						</a>
						{#if lead.email}
							<div class="text-xs text-[var(--color-text-muted)]">{lead.email}</div>
						{/if}
					</td>
					<td class="px-3 py-2 text-[var(--color-text-secondary)]">{lead.branche}</td>
					<td class="px-3 py-2 text-[var(--color-text-secondary)]">{lead.plz} {lead.ort}</td>
					<td class="px-3 py-2">
						<select value={lead.segment}
							onchange={(e) => updateSegment(lead, (e.target as HTMLSelectElement).value as Segment)}
							class="bg-transparent border border-transparent hover:border-[var(--color-surface-500)] rounded px-1 py-0.5 text-xs font-bold cursor-pointer focus:outline-none"
							style="color: {getSegmentColor(lead.segment)}"
						>
							{#each SEGMENTS as seg}
								<option value={seg} class="bg-[var(--color-surface-700)]">{seg}</option>
							{/each}
						</select>
					</td>
					<td class="px-3 py-2">
						<select value={lead.status}
							onchange={(e) => updateStatus(lead, (e.target as HTMLSelectElement).value as LeadStatus)}
							class="bg-transparent border border-transparent hover:border-[var(--color-surface-500)] rounded px-1 py-0.5 text-xs cursor-pointer text-[var(--color-text-secondary)] focus:outline-none"
						>
							{#each STATUSES as s}
								<option value={s} class="bg-[var(--color-surface-700)]">{s}</option>
							{/each}
						</select>
					</td>
					<td class="px-3 py-2 text-[var(--color-text-secondary)] text-xs">{lead.ansprechpartner || '—'}</td>
				</tr>
			{:else}
				<tr>
					<td colspan="7" class="px-3 py-8 text-center text-[var(--color-text-muted)]">Keine Leads gefunden</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
