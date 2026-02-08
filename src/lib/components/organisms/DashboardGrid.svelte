<script lang="ts">
	import StatCard from '$lib/components/molecules/StatCard.svelte';
	import ScoreBadge from '$lib/components/atoms/ScoreBadge.svelte';
	import Badge from '$lib/components/atoms/Badge.svelte';
	import { leads } from '$lib/stores/leads';
	import { getSegmentColor, getScoreColor } from '$lib/utils/scoring';
	import type { Segment, LeadStatus } from '$lib/types/lead';

	const allLeads = $derived($leads);
	const loading = $derived(allLeads.length === 0 && !leads.loaded);
	const total = $derived(allLeads.length);
	const avgScore = $derived(total > 0 ? Math.round(allLeads.reduce((s, l) => s + l.score, 0) / total) : 0);
	const mitKontakt = $derived(allLeads.filter(l => l.ansprechpartner).length);
	const hotCount = $derived(allLeads.filter(l => l.segment === 'HOT').length);

	const segmentCounts = $derived(
		(['HOT', 'WARM', 'COLD', 'DISQUALIFIED'] as Segment[]).map(seg => ({
			segment: seg,
			count: allLeads.filter(l => l.segment === seg).length,
			color: getSegmentColor(seg),
			pct: total > 0 ? Math.round(allLeads.filter(l => l.segment === seg).length / total * 100) : 0
		}))
	);

	const statusCounts = $derived(
		(['Neu', 'Kontaktiert', 'Interessiert', 'Angebot', 'Gewonnen', 'Verloren'] as LeadStatus[]).map(s => ({
			status: s,
			count: allLeads.filter(l => l.status === s).length
		}))
	);

	const scoreDistribution = $derived(() => {
		const buckets = [0, 0, 0, 0, 0]; // 0-19, 20-39, 40-59, 60-79, 80-100
		for (const l of allLeads) {
			const b = Math.min(Math.floor(l.score / 20), 4);
			buckets[b]++;
		}
		const max = Math.max(...buckets, 1);
		return buckets.map((count, i) => ({
			label: `${i * 20}-${i === 4 ? 100 : (i + 1) * 20 - 1}`,
			count,
			pct: Math.round(count / max * 100),
			color: getScoreColor(i * 20 + 10)
		}));
	});

	const topBranchen = $derived(() => {
		const map: Record<string, number> = {};
		for (const l of allLeads) {
			if (l.branche) map[l.branche] = (map[l.branche] || 0) + 1;
		}
		const sorted = Object.entries(map).sort((a, b) => b[1] - a[1]).slice(0, 6);
		const max = Math.max(sorted[0]?.[1] ?? 1, 1);
		return sorted.map(([name, count]) => ({ name, count, pct: Math.round(count / max * 100) }));
	});

	const recentLeads = $derived(
		[...allLeads].sort((a, b) => new Date(b.erstelltAm).getTime() - new Date(a.erstelltAm).getTime()).slice(0, 5)
	);

	const topLeads = $derived(
		[...allLeads].sort((a, b) => b.score - a.score).slice(0, 5)
	);
</script>

{#if loading}
	<div class="space-y-6 stagger">
		<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
			{#each [1,2,3,4] as _}
				<div class="panel p-4"><div class="skeleton h-4 w-20 mb-2"></div><div class="skeleton h-8 w-16"></div></div>
			{/each}
		</div>
		<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
			{#each [1,2,3,4] as _}
				<div class="panel p-4"><div class="skeleton h-4 w-full mb-2"></div><div class="skeleton h-6 w-12"></div></div>
			{/each}
		</div>
	</div>
{:else if total === 0}
	<div class="flex flex-col items-center justify-center py-20 text-center">
		<div class="text-6xl mb-4 opacity-20">▦</div>
		<h2 class="text-lg font-bold text-[var(--color-text-primary)] mb-2">Noch keine Leads</h2>
		<p class="text-sm text-[var(--color-text-muted)] mb-6 max-w-md">Leg deinen ersten Lead an oder importiere eine CSV/JSON-Datei um loszulegen.</p>
		<div class="flex gap-3">
			<a href="/leads/new" class="px-4 py-2 bg-[var(--color-accent)] text-black text-sm font-bold rounded-md hover:brightness-110 transition-all">+ Neuer Lead</a>
			<a href="/import" class="px-4 py-2 bg-[var(--color-surface-600)] text-[var(--color-text-primary)] text-sm font-medium rounded-md hover:bg-[var(--color-surface-500)] transition-all">Import</a>
		</div>
	</div>
{:else}
	<div class="space-y-6 stagger">
		<!-- Stats Row -->
		<div class="grid grid-cols-2 md:grid-cols-4 gap-3">
			<StatCard label="Gesamt" value={total} icon="▦" />
			<StatCard label="Ø Score" value={avgScore} color="var(--color-accent)" icon="◈" />
			<StatCard label="HOT Leads" value={hotCount} color="var(--color-hot)" icon="◉" pulse={hotCount > 0} />
			<StatCard label="Kontaktrate" value="{total > 0 ? Math.round(mitKontakt / total * 100) : 0}%" color="var(--color-success)" icon="◆" />
		</div>

		<!-- Segment Distribution -->
		<div class="panel">
			<div class="panel-header">Segment-Verteilung</div>
			<div class="p-4">
				<div class="flex gap-1 h-8 rounded overflow-hidden mb-3">
					{#each segmentCounts as seg}
						{#if seg.count > 0}
							<div
								class="transition-all duration-500 relative group cursor-default"
								style="width: {seg.pct}%; background: {seg.color}; min-width: {seg.count > 0 ? '24px' : '0'}"
								title="{seg.segment}: {seg.count} ({seg.pct}%)"
							>
								<span class="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-white drop-shadow-sm">
									{seg.count}
								</span>
							</div>
						{/if}
					{/each}
				</div>
				<div class="flex flex-wrap gap-4">
					{#each segmentCounts as seg}
						<div class="flex items-center gap-2">
							<div class="w-2.5 h-2.5 rounded-full {seg.segment === 'HOT' && seg.count > 0 ? 'animate-pulse-hot' : ''}" style="background: {seg.color}"></div>
							<span class="text-xs text-[var(--color-text-secondary)]">{seg.segment}</span>
							<span class="text-xs font-bold font-mono" style="color: {seg.color}">{seg.count}</span>
						</div>
					{/each}
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<!-- Score Distribution Chart -->
			<div class="panel">
				<div class="panel-header">Score-Verteilung</div>
				<div class="p-4">
					<div class="flex items-end gap-2 h-32">
						{#each scoreDistribution() as bucket}
							<div class="flex-1 flex flex-col items-center gap-1">
								<span class="text-[10px] font-mono font-bold" style="color: {bucket.color}">{bucket.count}</span>
								<div
									class="w-full rounded-t transition-all duration-700"
									style="height: {Math.max(bucket.pct, 4)}%; background: {bucket.color}; opacity: 0.8"
								></div>
								<span class="text-[9px] font-mono text-[var(--color-text-muted)]">{bucket.label}</span>
							</div>
						{/each}
					</div>
				</div>
			</div>

			<!-- Status Pipeline -->
			<div class="panel">
				<div class="panel-header">Pipeline</div>
				<div class="p-4 space-y-2">
					{#each statusCounts as s}
						<div class="flex items-center gap-3">
							<span class="text-xs text-[var(--color-text-secondary)] w-24 truncate">{s.status}</span>
							<div class="flex-1 h-5 bg-[var(--color-surface-700)] rounded overflow-hidden">
								<div
									class="h-full rounded transition-all duration-700 flex items-center px-2"
									style="width: {total > 0 ? Math.max(s.count / total * 100, s.count > 0 ? 8 : 0) : 0}%;
										background: {s.status === 'Gewonnen' ? 'var(--color-success)' : s.status === 'Verloren' ? 'var(--color-error)' : 'var(--color-accent)'}; opacity: 0.7"
								>
									{#if s.count > 0}
										<span class="text-[10px] font-bold text-white drop-shadow-sm">{s.count}</span>
									{/if}
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Top Branchen -->
			<div class="panel">
				<div class="panel-header">Top Branchen</div>
				<div class="p-4 space-y-2">
					{#each topBranchen() as b}
						<div class="flex items-center gap-3">
							<span class="text-xs text-[var(--color-text-secondary)] w-28 truncate">{b.name}</span>
							<div class="flex-1 h-4 bg-[var(--color-surface-700)] rounded overflow-hidden">
								<div class="h-full bg-[var(--color-info)] rounded transition-all duration-700 opacity-50" style="width: {b.pct}%"></div>
							</div>
							<span class="text-xs font-mono font-bold text-[var(--color-text-secondary)]">{b.count}</span>
						</div>
					{:else}
						<p class="text-xs text-[var(--color-text-muted)]">Keine Branchen-Daten</p>
					{/each}
				</div>
			</div>

			<!-- Top Leads by Score -->
			<div class="panel">
				<div class="panel-header">Top 5 Leads</div>
				<div class="divide-y divide-[var(--color-surface-700)]">
					{#each topLeads as lead, i}
						<a href="/leads/{lead.id}" class="flex items-center justify-between px-4 py-3 hover:bg-[var(--color-surface-700)] transition-colors group">
							<div class="flex items-center gap-3">
								<span class="text-xs font-mono text-[var(--color-text-muted)] w-4">{i + 1}</span>
								<div>
									<div class="text-sm font-medium text-[var(--color-text-primary)] group-hover:text-[var(--color-accent)] transition-colors">{lead.firma}</div>
									<div class="text-[10px] text-[var(--color-text-muted)]">{lead.branche} · {lead.ort}</div>
								</div>
							</div>
							<div class="flex items-center gap-2">
								<ScoreBadge score={lead.score} />
								<Badge color={getSegmentColor(lead.segment)}>{lead.segment}</Badge>
							</div>
						</a>
					{/each}
				</div>
			</div>
		</div>

		<!-- Recent Leads -->
		{#if recentLeads.length > 0}
			<div class="panel">
				<div class="panel-header">Zuletzt hinzugefügt</div>
				<div class="divide-y divide-[var(--color-surface-700)]">
					{#each recentLeads as lead}
						<a href="/leads/{lead.id}" class="flex items-center justify-between px-4 py-3 hover:bg-[var(--color-surface-700)] transition-colors group">
							<div>
								<div class="text-sm font-medium text-[var(--color-text-primary)] group-hover:text-[var(--color-accent)] transition-colors">{lead.firma}</div>
								<div class="text-[10px] text-[var(--color-text-muted)]">{lead.branche} · {lead.ort} · {new Date(lead.erstelltAm).toLocaleDateString('de-DE')}</div>
							</div>
							<div class="flex items-center gap-2">
								<ScoreBadge score={lead.score} />
								<Badge color={getSegmentColor(lead.segment)}>{lead.segment}</Badge>
								<span class="text-[10px] px-2 py-0.5 rounded bg-[var(--color-surface-600)] text-[var(--color-text-muted)]">{lead.status}</span>
							</div>
						</a>
					{/each}
				</div>
			</div>
		{/if}
	</div>
{/if}
