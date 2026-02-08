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

	function sort(col: string) { onsort?.(col); }

	async function updateStatus(lead: Lead, status: LeadStatus) {
		await leads.update_lead(lead.id, { status }, `Status geändert: ${status}`);
	}

	async function updateSegment(lead: Lead, segment: Segment) {
		await leads.update_lead(lead.id, { segment, segmentManuell: true }, `Segment manuell: ${segment}`);
	}

	function sortIcon(col: string): string {
		if (sortBy !== col) return '⇅';
		return sortDir === 'asc' ? '↑' : '↓';
	}

	const columns = [
		{ key: 'score', label: 'Score', w: 'w-16' },
		{ key: 'firma', label: 'Firma', w: 'min-w-[160px]' },
		{ key: 'branche', label: 'Branche', w: 'w-28 hidden md:table-cell' },
		{ key: 'ort', label: 'Ort', w: 'w-28 hidden lg:table-cell' },
		{ key: 'segment', label: 'Segment', w: 'w-28' },
		{ key: 'status', label: 'Status', w: 'w-32 hidden sm:table-cell' },
		{ key: 'ansprechpartner', label: 'Kontakt', w: 'w-28 hidden xl:table-cell' },
		{ key: 'kiScore', label: 'KI', w: 'w-16 hidden xl:table-cell' }
	];
</script>

<div class="overflow-x-auto">
	<table class="w-full text-sm">
		<thead>
			<tr class="border-b border-[var(--color-surface-600)]">
				{#each columns as col}
					<th class="{col.w} text-left px-3 py-2.5 text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest cursor-pointer hover:text-[var(--color-accent)] select-none transition-colors"
						onclick={() => sort(col.key)}>
						{col.label} <span class="text-[9px] opacity-50">{sortIcon(col.key)}</span>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each filteredLeads as lead, i (lead.id)}
				<tr class="border-b border-[var(--color-surface-700)] hover:bg-[var(--color-surface-700)] transition-all duration-150 group"
					style="animation-delay: {Math.min(i * 20, 300)}ms"
				>
					<td class="px-3 py-2.5"><ScoreBadge score={lead.score} /></td>
					<td class="px-3 py-2.5">
						<a href="/leads/{lead.id}" class="text-[var(--color-text-primary)] group-hover:text-[var(--color-accent)] font-medium transition-colors">
							{lead.firma || '(Ohne Name)'}
						</a>
						{#if lead.email}
							<div class="text-[10px] text-[var(--color-text-muted)] truncate max-w-[200px]">{lead.email}</div>
						{/if}
					</td>
					<td class="px-3 py-2.5 text-[var(--color-text-secondary)] text-xs hidden md:table-cell">{lead.branche}</td>
					<td class="px-3 py-2.5 text-[var(--color-text-muted)] text-xs hidden lg:table-cell font-mono">{lead.plz} {lead.ort}</td>
					<td class="px-3 py-2.5">
						<select value={lead.segment}
							onchange={(e) => updateSegment(lead, (e.target as HTMLSelectElement).value as Segment)}
							class="bg-transparent border border-transparent hover:border-[var(--color-surface-400)] rounded px-1 py-0.5 text-[10px] font-bold cursor-pointer focus:outline-none transition-colors"
							style="color: {getSegmentColor(lead.segment)}"
						>
							{#each SEGMENTS as seg}
								<option value={seg} class="bg-[var(--color-surface-700)]">{seg}</option>
							{/each}
						</select>
					</td>
					<td class="px-3 py-2.5 hidden sm:table-cell">
						<select value={lead.status}
							onchange={(e) => updateStatus(lead, (e.target as HTMLSelectElement).value as LeadStatus)}
							class="bg-transparent border border-transparent hover:border-[var(--color-surface-400)] rounded px-1 py-0.5 text-[10px] cursor-pointer text-[var(--color-text-secondary)] focus:outline-none transition-colors"
						>
							{#each STATUSES as s}
								<option value={s} class="bg-[var(--color-surface-700)]">{s}</option>
							{/each}
						</select>
					</td>
					<td class="px-3 py-2.5 text-[var(--color-text-muted)] text-[10px] hidden xl:table-cell">{lead.ansprechpartner || '—'}</td>
					<td class="px-3 py-2.5 hidden xl:table-cell">
						{#if lead.kiScore != null}
							<span class="text-[10px] font-mono font-bold text-[var(--color-accent)]">{lead.kiScore}</span>
							{#if lead.kiSegment}
								<span class="text-[9px] text-[var(--color-text-muted)] ml-1">{lead.kiSegment}</span>
							{/if}
						{:else}
							<span class="text-[10px] text-[var(--color-text-muted)]">—</span>
						{/if}
					</td>
				</tr>
			{:else}
				<tr>
					<td colspan="8" class="px-4 py-16 text-center">
						<div class="text-4xl opacity-10 mb-3">☰</div>
						<p class="text-sm text-[var(--color-text-muted)]">Keine Leads gefunden</p>
						<p class="text-xs text-[var(--color-text-muted)] mt-1">Passe die Filter an oder erstelle einen neuen Lead</p>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
