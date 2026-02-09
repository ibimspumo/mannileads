<script lang="ts">
	import StatCard from '$lib/components/molecules/StatCard.svelte';
	import ScoreBadge from '$lib/components/atoms/ScoreBadge.svelte';
	import Badge from '$lib/components/atoms/Badge.svelte';
	import { getSegmentColor, getScoreColor } from '$lib/utils/scoring';
	import { convex, api } from '$lib/convex';
	import type { Segment, LeadStatus } from '$lib/types/lead';

	let loading = $state(true);
	let stats = $state<any>(null);
	let topLeads = $state<any[]>([]);
	let recentLeads = $state<any[]>([]);

	async function loadData() {
		loading = true;
		try {
			// Load stats from server action + top/recent from query (all paginated server-side)
			const [statsData, trData] = await Promise.all([
				convex.query(api.leads.stats, {}),
				convex.query(api.leads.topAndRecent, { limit: 10 }),
			]);
			stats = statsData;
			topLeads = (trData.topLeads || []).map((d: any) => ({ ...d, id: d._id }));
			recentLeads = (trData.recentLeads || []).map((d: any) => ({ ...d, id: d._id }));
		} catch (e) {
			console.error('Dashboard load error:', e);
		} finally {
			loading = false;
		}
	}

	// Load on mount
	$effect(() => { loadData(); });

	const segmentCounts = $derived(
		stats ? (['HOT', 'WARM', 'COLD', 'DISQUALIFIED'] as Segment[]).map(seg => ({
			segment: seg,
			count: stats.segments[seg] || 0,
			color: getSegmentColor(seg),
			pct: stats.total > 0 ? Math.round((stats.segments[seg] || 0) / stats.total * 100) : 0
		})) : []
	);

	const statusCounts = $derived(
		stats ? (['Neu', 'Kontaktiert', 'Interessiert', 'Angebot', 'Gewonnen', 'Verloren'] as LeadStatus[]).map(s => ({
			status: s,
			count: stats.statuses[s] || 0
		})) : []
	);

	const scoreDistributionData = $derived(() => {
		if (!stats) return [];
		const buckets = stats.scoreDistribution as number[];
		const max = Math.max(...buckets, 1);
		return buckets.map((count: number, i: number) => ({
			label: `${i * 20}-${i === 4 ? 100 : (i + 1) * 20 - 1}`,
			count,
			pct: Math.round(count / max * 100),
			color: getScoreColor(i * 20 + 10)
		}));
	});

	const topBranchenData = $derived(() => {
		if (!stats) return [];
		const sorted = Object.entries(stats.branchen as Record<string, number>).sort((a, b) => b[1] - a[1]);
		const max = Math.max(sorted[0]?.[1] ?? 1, 1);
		return sorted.map(([name, count]) => ({ name, count, pct: Math.round(count / max * 100) }));
	});
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
{:else if !stats || stats.total === 0}
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
			<StatCard label="Gesamt" value={stats.total} icon="▦" />
			<StatCard label="Ø Score" value={stats.avgScore} color="var(--color-accent)" icon="◈" />
			<StatCard label="HOT Leads" value={stats.segments.HOT || 0} color="var(--color-hot)" icon="◉" pulse={(stats.segments.HOT || 0) > 0} />
			<StatCard label="Mit Email" value="{stats.total > 0 ? Math.round(stats.mitKontakt / stats.total * 100) : 0}%" color="var(--color-success)" icon="◆" />
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
						{#each scoreDistributionData() as bucket}
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
									style="width: {stats.total > 0 ? Math.max(s.count / stats.total * 100, s.count > 0 ? 8 : 0) : 0}%;
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
			<div class="panel flex flex-col" style="max-height: 600px;">
				<div class="panel-header shrink-0">Branchen ({topBranchenData().length})</div>
				<div class="p-4 space-y-1.5 overflow-y-auto flex-1">
					{#each topBranchenData() as b}
						<div class="flex items-center gap-3">
							<span class="text-xs text-[var(--color-text-secondary)] w-28 truncate" title={b.name}>{b.name}</span>
							<div class="flex-1 h-3.5 bg-[var(--color-surface-700)] rounded overflow-hidden">
								<div class="h-full bg-[var(--color-info)] rounded transition-all duration-700 opacity-50" style="width: {b.pct}%"></div>
							</div>
							<span class="text-[11px] font-mono font-bold text-[var(--color-text-secondary)] w-8 text-right">{b.count}</span>
						</div>
					{:else}
						<p class="text-xs text-[var(--color-text-muted)]">Keine Branchen-Daten</p>
					{/each}
				</div>
			</div>

			<!-- Top Leads by Score -->
			<div class="panel flex flex-col" style="max-height: 600px;">
				<div class="panel-header shrink-0">Top 10 Leads</div>
				<div class="divide-y divide-[var(--color-surface-700)] overflow-y-auto flex-1">
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
