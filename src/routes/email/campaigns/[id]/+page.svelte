<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	
	
	import { convex, api } from '$lib/convex';

	

	let campaign = $state<any>(null);
	let sends = $state<any[]>([]);
	let loading = $state(true);
	let processing = $state(false);

	const campaignId = $derived($page.params.id);

	onMount(async () => {
		await loadCampaign();
		// Auto-refresh stats every 5 seconds if campaign is sending
		const interval = setInterval(async () => {
			if (campaign?.status === 'sending' || campaign?.status === 'queued') {
				await loadCampaign();
			}
		}, 5000);

		return () => clearInterval(interval);
	});

	async function loadCampaign() {
		try {
			campaign = await convex.query(api.email.getCampaign, { id: campaignId as any });
			sends = await convex.query(api.email.listSends, { campaignId: campaignId as any, limit: 50 });
		} catch (error) {
			console.error('Failed to load campaign:', error);
		} finally {
			loading = false;
		}
	}

	async function startCampaign() {
		if (!confirm(`Kampagne starten? ${campaign.totalLeads || 0} Emails werden versendet.`)) return;
		processing = true;
		try {
			await convex.action(api.emailSending.startCampaign, { campaignId: campaignId as any });
			await loadCampaign();
			alert('Kampagne wurde gestartet! Emails werden in die Queue gelegt.');
		} catch (error) {
			console.error('Failed to start campaign:', error);
			alert('Fehler beim Starten: ' + error);
		} finally {
			processing = false;
		}
	}

	async function pauseCampaign() {
		processing = true;
		try {
			await convex.mutation(api.email.updateCampaign, {
				id: campaignId as any,
				status: 'paused'
			});
			await loadCampaign();
		} catch (error) {
			console.error('Failed to pause campaign:', error);
			alert('Fehler beim Pausieren: ' + error);
		} finally {
			processing = false;
		}
	}

	async function processSendQueue() {
		processing = true;
		try {
			await convex.action(api.emailSending.processSendQueue, { batchSize: 10 });
			await loadCampaign();
			alert('Batch verarbeitet!');
		} catch (error) {
			console.error('Failed to process queue:', error);
			alert('Fehler beim Versand: ' + error);
		} finally {
			processing = false;
		}
	}

	function formatPercent(n: number) {
		return n ? (n * 100).toFixed(1) + '%' : '0%';
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleString('de-DE', {
			day: '2-digit',
			month: '2-digit',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function statusColor(status: string) {
		switch (status) {
			case 'queued':
				return 'text-[var(--color-text-muted)]';
			case 'sending':
			case 'sent':
				return 'text-[var(--color-accent)]';
			case 'delivered':
				return 'text-[var(--color-success)]';
			case 'opened':
				return 'text-[var(--color-info)]';
			case 'clicked':
				return 'text-[var(--color-accent)]';
			case 'bounced':
			case 'failed':
				return 'text-[var(--color-error)]';
			default:
				return 'text-[var(--color-text-secondary)]';
		}
	}
</script>

<div class="space-y-6 animate-fade-in">
	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="skeleton w-32 h-32"></div>
		</div>
	{:else if !campaign}
		<div class="panel p-8 text-center">
			<p class="text-[var(--color-error)]">Kampagne nicht gefunden.</p>
			<a href="/email" class="text-[var(--color-accent)] hover:underline mt-2 inline-block">
				← Zurück zur Übersicht
			</a>
		</div>
	{:else}
		<!-- Header -->
		<div class="flex items-start justify-between">
			<div>
				<h1 class="text-2xl font-bold font-mono tracking-tight text-[var(--color-accent)]">
					{campaign.name}
				</h1>
				<div class="flex items-center gap-2 mt-2">
					<span
						class="inline-block px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider rounded {campaign.status ===
						'draft'
							? 'bg-[var(--color-surface-600)] text-[var(--color-text-muted)]'
							: campaign.status === 'queued' || campaign.status === 'sending'
								? 'bg-[var(--color-accent)] text-[var(--color-surface-900)]'
								: campaign.status === 'sent'
									? 'bg-[var(--color-success)] text-[var(--color-surface-900)]'
									: 'bg-[var(--color-surface-600)] text-[var(--color-text-muted)]'}"
					>
						{campaign.status.toUpperCase()}
					</span>
					<span class="text-xs text-[var(--color-text-muted)]">
						{campaign.account?.name} • {campaign.template?.name}
					</span>
				</div>
			</div>
			<div class="flex gap-2">
				<a
					href="/email"
					class="px-3 py-1.5 text-xs font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded transition-all"
				>
					← ZURÜCK
				</a>
				{#if campaign.status === 'draft'}
					<button
						onclick={startCampaign}
						disabled={processing}
						class="px-3 py-1.5 text-xs font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 disabled:opacity-50 text-[var(--color-surface-900)] rounded transition-all shadow-[0_0_12px_rgba(255,165,2,0.3)]"
					>
						{processing ? 'STARTE...' : '▶ KAMPAGNE STARTEN'}
					</button>
				{:else if campaign.status === 'queued'}
					<button
						onclick={processSendQueue}
						disabled={processing}
						class="px-3 py-1.5 text-xs font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 disabled:opacity-50 text-[var(--color-surface-900)] rounded transition-all"
					>
						{processing ? 'SENDE...' : '📧 BATCH SENDEN'}
					</button>
					<button
						onclick={pauseCampaign}
						disabled={processing}
						class="px-3 py-1.5 text-xs font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] rounded transition-all"
					>
						⏸ PAUSIEREN
					</button>
				{:else if campaign.status === 'paused'}
					<button
						onclick={processSendQueue}
						disabled={processing}
						class="px-3 py-1.5 text-xs font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 disabled:opacity-50 text-[var(--color-surface-900)] rounded transition-all"
					>
						{processing ? 'SENDE...' : '▶ FORTSETZEN'}
					</button>
				{/if}
			</div>
		</div>

		<!-- Stats -->
		<div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 stagger">
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Queue
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-text-primary)]">
						{campaign.totalQueued}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Gesendet
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-accent)]">
						{campaign.totalSent}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Zugestellt
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-success)]">
						{campaign.totalDelivered}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Geöffnet
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-accent)]">
						{campaign.totalOpened}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Geklickt
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-info)]">
						{campaign.totalClicked}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Bounced
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-error)]">
						{campaign.totalBounced}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Open Rate
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-accent)]">
						{formatPercent(campaign.openRate)}
					</div>
				</div>
			</div>
			<div class="panel">
				<div class="p-3">
					<div class="text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase mb-1">
						Click Rate
					</div>
					<div class="text-2xl font-mono font-bold text-[var(--color-info)]">
						{formatPercent(campaign.clickRate)}
					</div>
				</div>
			</div>
		</div>

		<!-- Sends -->
		<div class="panel">
			<div class="panel-header">Email Sends</div>
			<div class="overflow-x-auto">
				{#if sends.length === 0}
					<div class="p-8 text-center text-sm text-[var(--color-text-muted)]">
						Noch keine Sends vorhanden.
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
									Empfänger
								</th>
								<th
									class="text-left px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Betreff
								</th>
								<th
									class="text-left px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Queue Time
								</th>
								<th
									class="text-left px-3 py-2 text-[10px] font-mono font-bold text-[var(--color-text-muted)] tracking-widest uppercase"
								>
									Sent At
								</th>
							</tr>
						</thead>
						<tbody>
							{#each sends as send}
								<tr
									class="border-b border-[var(--color-surface-700)] hover:bg-[var(--color-surface-700)] transition-colors"
								>
									<td class="px-3 py-2">
										<span class="text-xs font-mono font-bold {statusColor(send.status)}">
											{send.status.toUpperCase()}
										</span>
									</td>
									<td class="px-3 py-2 text-[var(--color-text-primary)] font-mono text-xs">
										{send.to}
									</td>
									<td class="px-3 py-2 text-[var(--color-text-secondary)] text-xs truncate max-w-xs">
										{send.subject}
									</td>
									<td class="px-3 py-2 text-[var(--color-text-muted)] text-xs">
										{formatDate(send.queuedAt)}
									</td>
									<td class="px-3 py-2 text-[var(--color-text-muted)] text-xs">
										{send.sentAt ? formatDate(send.sentAt) : '—'}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}
			</div>
		</div>
	{/if}
</div>
