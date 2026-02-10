<script lang="ts">
	import { onMount } from 'svelte';
	import { ConvexHttpClient } from 'convex/browser';
	import { PUBLIC_CONVEX_URL } from '$env/static/public';
	import { api } from '$lib/convex/_generated/api';

	const client = new ConvexHttpClient(PUBLIC_CONVEX_URL);

	let campaigns = $state<any[]>([]);
	let recentEvents = $state<any[]>([]);
	let loading = $state(true);

	// Global stats
	let globalStats = $derived({
		totalSent: campaigns.reduce((sum, c) => sum + c.totalSent, 0),
		totalDelivered: campaigns.reduce((sum, c) => sum + c.totalDelivered, 0),
		totalOpened: campaigns.reduce((sum, c) => sum + c.totalOpened, 0),
		totalClicked: campaigns.reduce((sum, c) => sum + c.totalClicked, 0),
		totalBounced: campaigns.reduce((sum, c) => sum + c.totalBounced, 0),
		openRate:
			campaigns.reduce((sum, c) => sum + c.totalDelivered, 0) > 0
				? (campaigns.reduce((sum, c) => sum + c.totalOpened, 0) /
						campaigns.reduce((sum, c) => sum + c.totalDelivered, 0)) *
					100
				: 0,
		clickRate:
			campaigns.reduce((sum, c) => sum + c.totalOpened, 0) > 0
				? (campaigns.reduce((sum, c) => sum + c.totalClicked, 0) /
						campaigns.reduce((sum, c) => sum + c.totalOpened, 0)) *
					100
				: 0,
		bounceRate:
			campaigns.reduce((sum, c) => sum + c.totalSent, 0) > 0
				? (campaigns.reduce((sum, c) => sum + c.totalBounced, 0) /
						campaigns.reduce((sum, c) => sum + c.totalSent, 0)) *
					100
				: 0
	});

	onMount(async () => {
		try {
			campaigns = await client.query(api.email.listCampaigns);
			recentEvents = await client.query(api.email.listEvents, { limit: 20 });
		} catch (error) {
			console.error('Failed to load email data:', error);
		} finally {
			loading = false;
		}
	});

	function formatPercent(n: number) {
		return n.toFixed(1) + '%';
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleDateString('de-DE', {
			day: '2-digit',
			month: '2-digit',
			year: 'numeric'
		});
	}

	function formatDateTime(iso: string) {
		return new Date(iso).toLocaleString('de-DE', {
			day: '2-digit',
			month: '2-digit',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function statusColor(status: string) {
		switch (status) {
			case 'draft':
				return 'text-[var(--color-text-muted)]';
			case 'queued':
			case 'sending':
				return 'text-[var(--color-accent)]';
			case 'sent':
				return 'text-[var(--color-success)]';
			case 'paused':
				return 'text-[var(--color-warning)]';
			default:
				return 'text-[var(--color-text-secondary)]';
		}
	}

	function statusLabel(status: string) {
		const labels: Record<string, string> = {
			draft: 'ENTWURF',
			queued: 'WARTESCHLANGE',
			sending: 'SENDEN...',
			sent: 'GESENDET',
			paused: 'PAUSIERT'
		};
		return labels[status] || status.toUpperCase();
	}
</script>

<div class="space-y-6 animate-fade-in">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold font-mono tracking-tight text-[var(--color-accent)]">
				EMAIL CAMPAIGNS
			</h1>
			<p class="text-sm text-[var(--color-text-muted)] mt-1">
				Multi-Channel Lead Engagement System
			</p>
		</div>
		<div class="flex gap-2">
			<a
				href="/email/accounts"
				class="px-3 py-1.5 text-xs font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded transition-all"
			>
				ACCOUNTS
			</a>
			<a
				href="/email/templates"
				class="px-3 py-1.5 text-xs font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded transition-all"
			>
				TEMPLATES
			</a>
			<a
				href="/email/campaigns/new"
				class="px-3 py-1.5 text-xs font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded transition-all shadow-[0_0_12px_rgba(255,165,2,0.3)]"
			>
				+ NEUE KAMPAGNE
			</a>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="skeleton w-32 h-32"></div>
		</div>
	{:else}
		<!-- Global Stats -->
		<div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 stagger">
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Gesendet
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-text-primary)]">
						{globalStats.totalSent}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Zugestellt
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-success)]">
						{globalStats.totalDelivered}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Geöffnet
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-accent)]">
						{globalStats.totalOpened}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Geklickt
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-info)]">
						{globalStats.totalClicked}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Bounced
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-error)]">
						{globalStats.totalBounced}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Open Rate
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-accent)]">
						{formatPercent(globalStats.openRate)}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Click Rate
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-info)]">
						{formatPercent(globalStats.clickRate)}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Bounce Rate
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-error)]">
						{formatPercent(globalStats.bounceRate)}
					</div>
				</div>
			</div>
		</div>

		<!-- Campaigns -->
		<div class="panel">
			<div class="panel-header">Kampagnen</div>
			<div class="overflow-x-auto">
				{#if campaigns.length === 0}
					<div class="p-8 text-center">
						<p class="text-sm text-[var(--color-text-muted)]">Keine Kampagnen vorhanden.</p>
						<a
							href="/email/campaigns/new"
							class="inline-block mt-3 px-3 py-1.5 text-xs font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded transition-all"
						>
							+ ERSTE KAMPAGNE ERSTELLEN
						</a>
					</div>
				{:else}
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-[var(--color-surface-600)]">
								<th
									class="text-left px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Status
								</th>
								<th
									class="text-left px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Name
								</th>
								<th
									class="text-left px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Account
								</th>
								<th
									class="text-right px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Gesendet
								</th>
								<th
									class="text-right px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Opens
								</th>
								<th
									class="text-right px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Clicks
								</th>
								<th
									class="text-right px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Open Rate
								</th>
								<th
									class="text-left px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Erstellt
								</th>
								<th
									class="text-right px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Aktion
								</th>
							</tr>
						</thead>
						<tbody>
							{#each campaigns as campaign}
								<tr
									class="border-b border-[var(--color-surface-700)] hover:bg-[var(--color-surface-700)] transition-colors"
								>
									<td class="px-3 py-2">
										<span class="text-xs font-mono font-bold {statusColor(campaign.status)}">
											{statusLabel(campaign.status)}
										</span>
									</td>
									<td class="px-3 py-2">
										<a
											href="/email/campaigns/{campaign._id}"
											class="font-medium text-[var(--color-text-primary)] hover:text-[var(--color-accent)] transition-colors"
										>
											{campaign.name}
										</a>
									</td>
									<td class="px-3 py-2 text-[var(--color-text-secondary)] text-xs">
										{campaign.account?.name || '—'}
									</td>
									<td class="px-3 py-2 text-right font-mono text-[var(--color-text-primary)]">
										{campaign.totalSent}
									</td>
									<td class="px-3 py-2 text-right font-mono text-[var(--color-accent)]">
										{campaign.totalOpened}
									</td>
									<td class="px-3 py-2 text-right font-mono text-[var(--color-info)]">
										{campaign.totalClicked}
									</td>
									<td class="px-3 py-2 text-right font-mono text-[var(--color-accent)]">
										{formatPercent(campaign.openRate || 0)}
									</td>
									<td class="px-3 py-2 text-xs text-[var(--color-text-muted)]">
										{formatDate(campaign.createdAt)}
									</td>
									<td class="px-3 py-2 text-right">
										<a
											href="/email/campaigns/{campaign._id}"
											class="text-xs font-mono text-[var(--color-accent)] hover:underline"
										>
											DETAILS →
										</a>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}
			</div>
		</div>

		<!-- Recent Events -->
		{#if recentEvents.length > 0}
			<div class="panel">
				<div class="panel-header">Letzte Events</div>
				<div class="divide-y divide-[var(--color-surface-700)]">
					{#each recentEvents.slice(0, 10) as event}
						<div class="px-4 py-2 flex items-center justify-between text-xs">
							<div class="flex items-center gap-2">
								<span
									class="inline-block w-1.5 h-1.5 rounded-full {event.type === 'open'
										? 'bg-[var(--color-accent)]'
										: event.type === 'click'
											? 'bg-[var(--color-info)]'
											: event.type === 'bounce'
												? 'bg-[var(--color-error)]'
												: 'bg-[var(--color-warning)]'}"
								></span>
								<span class="font-mono font-bold text-[var(--color-text-secondary)] uppercase">
									{event.type}
								</span>
								<span class="text-[var(--color-text-muted)]">
									{formatDateTime(event.timestamp)}
								</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	{/if}
</div>
