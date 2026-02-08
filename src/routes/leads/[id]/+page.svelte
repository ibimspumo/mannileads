<script lang="ts">
	import { page } from '$app/stores';
	import { leads } from '$lib/stores/leads';
	import { goto } from '$app/navigation';
	import LeadForm from '$lib/components/organisms/LeadForm.svelte';
	import ScoreBadge from '$lib/components/atoms/ScoreBadge.svelte';
	import Badge from '$lib/components/atoms/Badge.svelte';
	import ScoreBreakdown from '$lib/components/molecules/ScoreBreakdown.svelte';
	import Button from '$lib/components/atoms/Button.svelte';
	import { getScoreBreakdown, getSegmentColor } from '$lib/utils/scoring';
	import type { Lead } from '$lib/types/lead';

	const lead = $derived($leads.find(l => l.id === $page.params.id));
	const breakdown = $derived(lead ? getScoreBreakdown(lead) : []);

	let editing = $state(false);

	function handleUpdate(data: Partial<Lead>) {
		if (!lead) return;
		leads.update_lead(lead.id, data, 'Bearbeitet');
		editing = false;
	}

	function handleDelete() {
		if (!lead) return;
		if (confirm(`"${lead.firma}" wirklich löschen?`)) {
			leads.remove(lead.id);
			goto('/leads');
		}
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
	}
</script>

<svelte:head>
	<title>{lead?.firma ?? 'Lead'} — ManniLeads</title>
</svelte:head>

{#if !lead}
	<div class="text-center py-12 text-[var(--color-text-muted)]">
		<p>Lead nicht gefunden.</p>
		<a href="/leads" class="text-[var(--color-accent)] hover:underline text-sm">← Zurück zur Liste</a>
	</div>
{:else if editing}
	<div class="max-w-3xl">
		<div class="flex items-center justify-between mb-6">
			<h1 class="text-xl font-bold text-[var(--color-text-primary)]">Bearbeiten: {lead.firma}</h1>
			<Button variant="ghost" size="sm" onclick={() => editing = false}>Abbrechen</Button>
		</div>
		<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-6">
			<LeadForm initial={lead} onsubmit={handleUpdate} submitLabel="Speichern" />
		</div>
	</div>
{:else}
	<div class="space-y-6">
		<!-- Header -->
		<div class="flex items-start justify-between">
			<div>
				<a href="/leads" class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-accent)]">← Leads</a>
				<h1 class="text-xl font-bold text-[var(--color-text-primary)] mt-1">{lead.firma}</h1>
				<div class="flex items-center gap-2 mt-1">
					<ScoreBadge score={lead.score} />
					<Badge color={getSegmentColor(lead.segment)}>{lead.segment}</Badge>
					<span class="text-xs text-[var(--color-text-muted)]">{lead.status}</span>
				</div>
			</div>
			<div class="flex gap-2">
				<Button variant="secondary" size="sm" onclick={() => editing = true}>Bearbeiten</Button>
				<Button variant="danger" size="sm" onclick={handleDelete}>Löschen</Button>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
			<!-- Main Info -->
			<div class="lg:col-span-2 space-y-4">
				<!-- Firma -->
				<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-4">
					<h3 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Firma</h3>
					<div class="grid grid-cols-2 gap-3 text-sm">
						<div><span class="text-[var(--color-text-muted)]">Branche:</span> <span class="text-[var(--color-text-primary)]">{lead.branche || '—'}</span></div>
						<div><span class="text-[var(--color-text-muted)]">Größe:</span> <span class="text-[var(--color-text-primary)]">{lead.groesse || '—'}</span></div>
						<div><span class="text-[var(--color-text-muted)]">PLZ/Ort:</span> <span class="text-[var(--color-text-primary)]">{lead.plz} {lead.ort}</span></div>
						<div><span class="text-[var(--color-text-muted)]">Website:</span>
							{#if lead.website}
								<a href={lead.website} target="_blank" class="text-[var(--color-accent)] hover:underline">{lead.website}</a>
							{:else}
								<span class="text-[var(--color-text-primary)]">—</span>
							{/if}
						</div>
					</div>
				</div>

				<!-- Kontakt -->
				<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-4">
					<h3 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Ansprechpartner</h3>
					<div class="grid grid-cols-2 gap-3 text-sm">
						<div><span class="text-[var(--color-text-muted)]">Name:</span> <span class="text-[var(--color-text-primary)]">{lead.ansprechpartner || '—'}</span></div>
						<div><span class="text-[var(--color-text-muted)]">Position:</span> <span class="text-[var(--color-text-primary)]">{lead.position || '—'}</span></div>
						<div><span class="text-[var(--color-text-muted)]">Email:</span> <span class="text-[var(--color-text-primary)]">{lead.email || '—'}</span></div>
						<div><span class="text-[var(--color-text-muted)]">Telefon:</span> <span class="text-[var(--color-text-primary)]">{lead.telefon || '—'}</span></div>
					</div>
				</div>

				<!-- Online -->
				<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-4">
					<h3 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Online-Präsenz</h3>
					<div class="grid grid-cols-2 gap-3 text-sm">
						<div><span class="text-[var(--color-text-muted)]">Website-Qualität:</span> <span class="text-[var(--color-text-primary)]">{'★'.repeat(lead.websiteQualitaet)}{'☆'.repeat(5 - lead.websiteQualitaet)}</span></div>
						<div><span class="text-[var(--color-text-muted)]">Social Media:</span> <span class="text-[var(--color-text-primary)]">{lead.socialMedia ? 'Ja' : 'Nein'}</span></div>
						<div><span class="text-[var(--color-text-muted)]">Google:</span> <span class="text-[var(--color-text-primary)]">{lead.googleBewertung || '—'}</span></div>
						{#if lead.socialMediaLinks}
							<div><span class="text-[var(--color-text-muted)]">Links:</span> <span class="text-[var(--color-text-primary)]">{lead.socialMediaLinks}</span></div>
						{/if}
					</div>
				</div>

				<!-- Notizen & KI -->
				{#if lead.notizen || lead.kiZusammenfassung}
					<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-4">
						{#if lead.kiZusammenfassung}
							<h3 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">KI-Zusammenfassung</h3>
							<p class="text-sm text-[var(--color-text-secondary)] mb-4 whitespace-pre-wrap">{lead.kiZusammenfassung}</p>
						{/if}
						{#if lead.notizen}
							<h3 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Notizen</h3>
							<p class="text-sm text-[var(--color-text-secondary)] whitespace-pre-wrap">{lead.notizen}</p>
						{/if}
					</div>
				{/if}

				<!-- Tags -->
				{#if lead.tags.length > 0}
					<div class="flex flex-wrap gap-1">
						{#each lead.tags as tag}
							<span class="px-2 py-0.5 rounded bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] text-xs">{tag}</span>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Sidebar -->
			<div class="space-y-4">
				<!-- Score Breakdown -->
				<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-4">
					<h3 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Score-Aufschlüsselung</h3>
					<ScoreBreakdown items={breakdown} />
					<div class="mt-3 pt-3 border-t border-[var(--color-surface-600)] flex items-center justify-between">
						<span class="text-sm font-bold text-[var(--color-text-primary)]">Gesamt</span>
						<ScoreBadge score={lead.score} />
					</div>
				</div>

				<!-- Timeline -->
				<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-4">
					<h3 class="text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Verlauf</h3>
					<div class="space-y-3">
						{#each [...lead.history].reverse() as entry}
							<div class="text-xs">
								<div class="text-[var(--color-text-muted)]">{formatDate(entry.timestamp)}</div>
								<div class="text-[var(--color-text-secondary)]"><span class="font-medium text-[var(--color-text-primary)]">{entry.aktion}</span> — {entry.details}</div>
							</div>
						{/each}
					</div>
				</div>

				<!-- Meta -->
				<div class="text-xs text-[var(--color-text-muted)] space-y-1">
					<div>Erstellt: {formatDate(lead.erstelltAm)}</div>
					<div>Bearbeitet: {formatDate(lead.bearbeitetAm)}</div>
					<div class="font-mono opacity-50">ID: {lead.id}</div>
				</div>
			</div>
		</div>
	</div>
{/if}
