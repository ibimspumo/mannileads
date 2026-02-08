<script lang="ts">
	import { page } from '$app/stores';
	import { leads } from '$lib/stores/leads';
	import { goto } from '$app/navigation';
	import LeadForm from '$lib/components/organisms/LeadForm.svelte';
	import ScoreBadge from '$lib/components/atoms/ScoreBadge.svelte';
	import Badge from '$lib/components/atoms/Badge.svelte';
	import ScoreBreakdown from '$lib/components/molecules/ScoreBreakdown.svelte';
	import Button from '$lib/components/atoms/Button.svelte';
	import { getScoreBreakdown, getSegmentColor, getScoreColor } from '$lib/utils/scoring';
	import type { Lead } from '$lib/types/lead';

	const lead = $derived($leads.find(l => l.id === $page.params.id));
	const breakdown = $derived(lead ? getScoreBreakdown(lead) : []);
	const totalMax = $derived(breakdown.reduce((s, i) => s + i.maxPunkte, 0));

	let editing = $state(false);
	let saving = $state(false);

	async function handleUpdate(data: Partial<Lead>) {
		if (!lead) return;
		saving = true;
		await leads.update_lead(lead.id, data, 'Bearbeitet');
		saving = false;
		editing = false;
	}

	async function handleDelete() {
		if (!lead) return;
		if (confirm(`"${lead.firma}" wirklich löschen?`)) {
			await leads.remove(lead.id);
			goto('/leads');
		}
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
	}

	function timeAgo(iso: string): string {
		const diff = Date.now() - new Date(iso).getTime();
		const mins = Math.floor(diff / 60000);
		if (mins < 60) return `vor ${mins}m`;
		const hours = Math.floor(mins / 60);
		if (hours < 24) return `vor ${hours}h`;
		const days = Math.floor(hours / 24);
		return `vor ${days}d`;
	}
</script>

<svelte:head>
	<title>{lead?.firma ?? 'Lead'} — ManniLeads</title>
</svelte:head>

{#if !lead}
	<div class="flex flex-col items-center justify-center py-20 text-center">
		<div class="text-5xl opacity-10 mb-4">?</div>
		<p class="text-sm text-[var(--color-text-muted)] mb-4">Lead nicht gefunden.</p>
		<a href="/leads" class="text-[var(--color-accent)] hover:underline text-sm">← Zurück zur Liste</a>
	</div>
{:else if editing}
	<div class="max-w-3xl animate-fade-in">
		<div class="flex items-center justify-between mb-6">
			<h1 class="text-xl font-bold text-[var(--color-text-primary)]">Bearbeiten: {lead.firma}</h1>
			<Button variant="ghost" size="sm" onclick={() => editing = false}>Abbrechen</Button>
		</div>
		{#if saving}
			<div class="panel p-8 text-center">
				<div class="text-2xl mb-2 animate-pulse-hot">◈</div>
				<p class="text-sm text-[var(--color-text-secondary)]">Wird gespeichert...</p>
			</div>
		{:else}
			<div class="panel p-6">
				<LeadForm initial={lead} onsubmit={handleUpdate} submitLabel="Speichern" />
			</div>
		{/if}
	</div>
{:else}
	<div class="space-y-6 animate-fade-in">
		<!-- Header -->
		<div class="flex items-start justify-between flex-wrap gap-4">
			<div>
				<a href="/leads" class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] hover:text-[var(--color-accent)] transition-colors">← Leads</a>
				<h1 class="text-2xl font-bold text-[var(--color-text-primary)] mt-1">{lead.firma}</h1>
				<div class="flex items-center gap-2 mt-2 flex-wrap">
					<ScoreBadge score={lead.score} />
					<Badge color={getSegmentColor(lead.segment)}>{lead.segment}</Badge>
					<span class="text-[10px] px-2 py-0.5 rounded bg-[var(--color-surface-600)] text-[var(--color-text-muted)]">{lead.status}</span>
					{#each lead.tags as tag}
						<span class="text-[10px] px-2 py-0.5 rounded bg-[var(--color-surface-600)] text-[var(--color-accent)] border border-[var(--color-accent)] border-opacity-20">{tag}</span>
					{/each}
				</div>
			</div>
			<div class="flex gap-2">
				<Button variant="secondary" size="sm" onclick={() => editing = true}>Bearbeiten</Button>
				<Button variant="danger" size="sm" onclick={handleDelete}>Löschen</Button>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- Main Info -->
			<div class="lg:col-span-2 space-y-4 stagger">
				<!-- Firma -->
				<div class="panel p-4">
					<h3 class="panel-header" style="padding: 0; border: none; margin-bottom: 0.75rem;">Firma</h3>
					<div class="grid grid-cols-2 gap-y-3 gap-x-6 text-sm">
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Branche</span><br><span class="text-[var(--color-text-primary)] font-medium">{lead.branche || '—'}</span></div>
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Größe</span><br><span class="text-[var(--color-text-primary)] font-medium">{lead.groesse || '—'}</span></div>
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Standort</span><br><span class="text-[var(--color-text-primary)] font-medium font-mono">{lead.plz} {lead.ort}</span></div>
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Website</span><br>
							{#if lead.website}
								<a href={lead.website} target="_blank" class="text-[var(--color-accent)] hover:underline text-sm">{lead.website}</a>
							{:else}
								<span class="text-[var(--color-text-muted)]">—</span>
							{/if}
						</div>
					</div>
				</div>

				<!-- Kontakt -->
				<div class="panel p-4">
					<h3 class="panel-header" style="padding: 0; border: none; margin-bottom: 0.75rem;">Ansprechpartner</h3>
					<div class="grid grid-cols-2 gap-y-3 gap-x-6 text-sm">
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Name</span><br><span class="text-[var(--color-text-primary)] font-medium">{lead.ansprechpartner || '—'}</span></div>
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Position</span><br><span class="text-[var(--color-text-primary)] font-medium">{lead.position || '—'}</span></div>
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Email</span><br><span class="text-[var(--color-text-primary)] font-medium">{lead.email || '—'}</span></div>
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Telefon</span><br><span class="text-[var(--color-text-primary)] font-medium font-mono">{lead.telefon || '—'}</span></div>
					</div>
				</div>

				<!-- Online-Präsenz -->
				<div class="panel p-4">
					<h3 class="panel-header" style="padding: 0; border: none; margin-bottom: 0.75rem;">Online-Präsenz</h3>
					<div class="grid grid-cols-2 gap-y-3 gap-x-6 text-sm">
						<div>
							<span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Website-Qualität</span><br>
							<div class="flex gap-0.5 mt-1">
								{#each [1,2,3,4,5] as star}
									<span class="text-sm {star <= lead.websiteQualitaet ? 'text-[var(--color-accent)]' : 'text-[var(--color-surface-500)]'}">★</span>
								{/each}
							</div>
						</div>
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Social Media</span><br>
							<span class="{lead.socialMedia ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]'} font-medium">{lead.socialMedia ? '✓ Vorhanden' : '✗ Nicht vorhanden'}</span>
						</div>
						<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Google-Bewertung</span><br><span class="text-[var(--color-text-primary)] font-medium">{lead.googleBewertung || '—'}</span></div>
						{#if lead.socialMediaLinks}
							<div><span class="text-[10px] uppercase tracking-wider text-[var(--color-text-muted)]">Social Links</span><br><span class="text-[var(--color-text-secondary)] text-xs">{lead.socialMediaLinks}</span></div>
						{/if}
					</div>
				</div>

				<!-- KI & Notizen -->
				{#if lead.kiZusammenfassung || lead.notizen}
					<div class="panel p-4 space-y-4">
						{#if lead.kiZusammenfassung}
							<div>
								<h3 class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-2">KI-Zusammenfassung</h3>
								<p class="text-sm text-[var(--color-text-secondary)] whitespace-pre-wrap leading-relaxed">{lead.kiZusammenfassung}</p>
							</div>
						{/if}
						{#if lead.notizen}
							<div>
								<h3 class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-2">Notizen</h3>
								<p class="text-sm text-[var(--color-text-secondary)] whitespace-pre-wrap leading-relaxed">{lead.notizen}</p>
							</div>
						{/if}
					</div>
				{/if}
			</div>

			<!-- Sidebar -->
			<div class="space-y-4 stagger">
				<!-- Score Visual -->
				<div class="panel p-4">
					<h3 class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-3">Score</h3>
					<!-- Big score display -->
					<div class="flex items-center justify-center mb-4">
						<div class="relative w-24 h-24 flex items-center justify-center">
							<svg class="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 100 100">
								<circle cx="50" cy="50" r="42" fill="none" stroke="var(--color-surface-600)" stroke-width="6" />
								<circle cx="50" cy="50" r="42" fill="none"
									stroke={getScoreColor(lead.score)}
									stroke-width="6"
									stroke-linecap="round"
									stroke-dasharray="{lead.score / 100 * 264} 264"
									class="transition-all duration-1000"
								/>
							</svg>
							<span class="text-2xl font-bold font-mono" style="color: {getScoreColor(lead.score)}">{lead.score}</span>
						</div>
					</div>
					<!-- Breakdown -->
					<ScoreBreakdown items={breakdown} />
					<div class="mt-3 pt-3 border-t border-[var(--color-surface-600)] flex items-center justify-between">
						<span class="text-xs font-bold text-[var(--color-text-primary)]">Gesamt</span>
						<span class="text-xs font-mono font-bold" style="color: {getScoreColor(lead.score)}">{lead.score}/{totalMax}</span>
					</div>
				</div>

				<!-- Timeline -->
				<div class="panel p-4">
					<h3 class="text-[10px] font-bold uppercase tracking-widest text-[var(--color-text-muted)] mb-3">Verlauf</h3>
					<div class="relative">
						<!-- Timeline line -->
						<div class="absolute left-[5px] top-2 bottom-2 w-px bg-[var(--color-surface-600)]"></div>
						<div class="space-y-4">
							{#each [...lead.history].reverse() as entry, i}
								<div class="flex gap-3 relative">
									<div class="w-[11px] h-[11px] rounded-full border-2 mt-0.5 flex-shrink-0 z-10
										{i === 0 ? 'border-[var(--color-accent)] bg-[var(--color-accent)]' : 'border-[var(--color-surface-400)] bg-[var(--color-surface-800)]'}">
									</div>
									<div class="text-xs min-w-0">
										<div class="font-medium text-[var(--color-text-primary)]">{entry.aktion}</div>
										<div class="text-[var(--color-text-muted)]">{entry.details}</div>
										<div class="text-[10px] text-[var(--color-text-muted)] mt-0.5 font-mono">{timeAgo(entry.timestamp)} · {formatDate(entry.timestamp)}</div>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>

				<!-- Meta -->
				<div class="panel p-4">
					<div class="text-[10px] text-[var(--color-text-muted)] space-y-1 font-mono">
						<div>Erstellt: {formatDate(lead.erstelltAm)}</div>
						<div>Bearbeitet: {formatDate(lead.bearbeitetAm)}</div>
						<div class="opacity-40 break-all">ID: {lead.id}</div>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
