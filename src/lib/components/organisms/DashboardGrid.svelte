<script lang="ts">
	import StatCard from '$lib/components/molecules/StatCard.svelte';
	import ScoreBadge from '$lib/components/atoms/ScoreBadge.svelte';
	import Badge from '$lib/components/atoms/Badge.svelte';
	import { leads } from '$lib/stores/leads';
	import { getSegmentColor } from '$lib/utils/scoring';
	import type { Segment } from '$lib/types/lead';

	const allLeads = $derived($leads);
	const total = $derived(allLeads.length);
	const avgScore = $derived(total > 0 ? Math.round(allLeads.reduce((s, l) => s + l.score, 0) / total) : 0);
	const mitKontakt = $derived(allLeads.filter(l => l.ansprechpartner).length);

	const segmentCounts = $derived(
		(['HOT', 'WARM', 'COLD', 'DISQUALIFIED'] as Segment[]).map(seg => ({
			segment: seg,
			count: allLeads.filter(l => l.segment === seg).length,
			color: getSegmentColor(seg)
		}))
	);

	const recentLeads = $derived(
		[...allLeads].sort((a, b) => new Date(b.erstelltAm).getTime() - new Date(a.erstelltAm).getTime()).slice(0, 5)
	);
</script>

<div class="space-y-6">
	<!-- Stats -->
	<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
		<StatCard label="Gesamt Leads" value={total} />
		<StatCard label="Ø Score" value={avgScore} color="var(--color-accent)" />
		<StatCard label="Mit Kontakt" value={mitKontakt} color="var(--color-success)" />
		<StatCard label="Ohne Kontakt" value={total - mitKontakt} color="var(--color-text-muted)" />
	</div>

	<!-- Segments -->
	<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
		{#each segmentCounts as seg}
			<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-4 flex items-center gap-3">
				<div class="w-3 h-3 rounded-full" style="background: {seg.color}"></div>
				<div>
					<div class="text-xs text-[var(--color-text-muted)] uppercase">{seg.segment}</div>
					<div class="text-lg font-bold tabular-nums" style="color: {seg.color}">{seg.count}</div>
				</div>
			</div>
		{/each}
	</div>

	<!-- Recent -->
	{#if recentLeads.length > 0}
		<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg">
			<div class="px-4 py-3 border-b border-[var(--color-surface-600)]">
				<h3 class="text-sm font-bold text-[var(--color-text-primary)] uppercase tracking-wider">Zuletzt hinzugefügt</h3>
			</div>
			<div class="divide-y divide-[var(--color-surface-700)]">
				{#each recentLeads as lead}
					<a href="/leads/{lead.id}" class="flex items-center justify-between px-4 py-3 hover:bg-[var(--color-surface-700)] transition-colors">
						<div>
							<div class="text-sm font-medium text-[var(--color-text-primary)]">{lead.firma}</div>
							<div class="text-xs text-[var(--color-text-muted)]">{lead.branche} · {lead.ort}</div>
						</div>
						<div class="flex items-center gap-2">
							<ScoreBadge score={lead.score} />
							<Badge color={getSegmentColor(lead.segment)}>{lead.segment}</Badge>
						</div>
					</a>
				{/each}
			</div>
		</div>
	{/if}
</div>
