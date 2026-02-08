<script lang="ts">
	import Input from '$lib/components/atoms/Input.svelte';
	import Select from '$lib/components/atoms/Select.svelte';
	import Textarea from '$lib/components/atoms/Textarea.svelte';
	import Button from '$lib/components/atoms/Button.svelte';
	import Tag from '$lib/components/atoms/Tag.svelte';
	import { BRANCHEN, STATUSES, SEGMENTS } from '$lib/types/lead';
	import type { Lead } from '$lib/types/lead';

	interface Props {
		initial?: Partial<Lead>;
		onsubmit: (data: Partial<Lead>) => void;
		submitLabel?: string;
	}
	let { initial = {}, onsubmit, submitLabel = 'Speichern' }: Props = $props();

	let firma = $state(initial.firma ?? '');
	let website = $state(initial.website ?? '');
	let branche = $state(initial.branche ?? '');
	let groesse = $state(initial.groesse ?? '');
	let plz = $state(initial.plz ?? '');
	let ort = $state(initial.ort ?? '');
	let ansprechpartner = $state(initial.ansprechpartner ?? '');
	let position = $state(initial.position ?? '');
	let email = $state(initial.email ?? '');
	let telefon = $state(initial.telefon ?? '');
	let websiteQualitaet = $state(initial.websiteQualitaet ?? 0);
	let socialMedia = $state(initial.socialMedia ?? false);
	let socialMediaLinks = $state(initial.socialMediaLinks ?? '');
	let googleBewertung = $state(initial.googleBewertung ?? '');
	let kiZusammenfassung = $state(initial.kiZusammenfassung ?? '');
	let segment = $state(initial.segment ?? 'COLD');
	let segmentManuell = $state(initial.segmentManuell ?? false);
	let tags = $state<string[]>(initial.tags ?? []);
	let status = $state(initial.status ?? 'Neu');
	let notizen = $state(initial.notizen ?? '');
	let newTag = $state('');

	function addTag() {
		const t = newTag.trim();
		if (t && !tags.includes(t)) {
			tags = [...tags, t];
		}
		newTag = '';
	}

	function removeTag(tag: string) {
		tags = tags.filter(t => t !== tag);
	}

	function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		onsubmit({
			firma, website, branche, groesse, plz, ort,
			ansprechpartner, position, email, telefon,
			websiteQualitaet, socialMedia, socialMediaLinks, googleBewertung,
			kiZusammenfassung, segment, segmentManuell, tags, status, notizen
		});
	}

	const brancheOptions = [{ value: '', label: 'Branche wählen...' }, ...BRANCHEN.map(b => ({ value: b, label: b }))];
	const statusOptions = STATUSES.map(s => ({ value: s, label: s }));
	const segmentOptions = SEGMENTS.map(s => ({ value: s, label: s }));
	const qualOptions = [0,1,2,3,4,5].map(n => ({ value: String(n), label: n === 0 ? 'Nicht bewertet' : '★'.repeat(n) }));
</script>

<form onsubmit={handleSubmit} class="space-y-6">
	<!-- Firma -->
	<fieldset class="space-y-3">
		<legend class="text-sm font-bold text-[var(--color-text-primary)] uppercase tracking-wider border-b border-[var(--color-surface-600)] pb-1 mb-2">Firma</legend>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
			<Input label="Firmenname *" bind:value={firma} required placeholder="z.B. Müller Handwerk GmbH" />
			<Input label="Website" bind:value={website} placeholder="https://..." />
			<Select label="Branche" options={brancheOptions} bind:value={branche} />
			<Input label="Größe (geschätzt)" bind:value={groesse} placeholder="z.B. 5-10 MA" />
			<Input label="PLZ" bind:value={plz} placeholder="19053" />
			<Input label="Ort" bind:value={ort} placeholder="Schwerin" />
		</div>
	</fieldset>

	<!-- Kontakt -->
	<fieldset class="space-y-3">
		<legend class="text-sm font-bold text-[var(--color-text-primary)] uppercase tracking-wider border-b border-[var(--color-surface-600)] pb-1 mb-2">Ansprechpartner</legend>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
			<Input label="Name" bind:value={ansprechpartner} placeholder="Max Mustermann" />
			<Input label="Position" bind:value={position} placeholder="Geschäftsführer" />
			<Input label="Email" type="email" bind:value={email} placeholder="max@firma.de" />
			<Input label="Telefon" type="tel" bind:value={telefon} placeholder="+49..." />
		</div>
	</fieldset>

	<!-- Online-Präsenz -->
	<fieldset class="space-y-3">
		<legend class="text-sm font-bold text-[var(--color-text-primary)] uppercase tracking-wider border-b border-[var(--color-surface-600)] pb-1 mb-2">Online-Präsenz</legend>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
			<Select label="Website-Qualität" options={qualOptions} value={String(websiteQualitaet)} onchange={(e) => websiteQualitaet = Number((e.target as HTMLSelectElement).value)} />
			<Input label="Google-Bewertung" bind:value={googleBewertung} placeholder="4.5 / 120 Bewertungen" />
			<div>
				<label class="flex items-center gap-2 text-sm text-[var(--color-text-secondary)] cursor-pointer">
					<input type="checkbox" bind:checked={socialMedia} class="rounded border-[var(--color-surface-500)] bg-[var(--color-surface-700)]" />
					Social Media vorhanden
				</label>
			</div>
			{#if socialMedia}
				<Input label="Social-Media-Links" bind:value={socialMediaLinks} placeholder="Instagram, Facebook..." />
			{/if}
		</div>
	</fieldset>

	<!-- Analyse -->
	<fieldset class="space-y-3">
		<legend class="text-sm font-bold text-[var(--color-text-primary)] uppercase tracking-wider border-b border-[var(--color-surface-600)] pb-1 mb-2">Analyse & Status</legend>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3">
			<Select label="Status" options={statusOptions} bind:value={status} />
			<div>
				<Select label="Segment" options={segmentOptions} bind:value={segment} />
				<label class="flex items-center gap-2 mt-1 text-xs text-[var(--color-text-muted)] cursor-pointer">
					<input type="checkbox" bind:checked={segmentManuell} class="rounded" />
					Manuell festlegen (kein Auto-Score)
				</label>
			</div>
		</div>
		<Textarea label="KI-Zusammenfassung" bind:value={kiZusammenfassung} placeholder="Automatische Analyse..." />
		<Textarea label="Notizen" bind:value={notizen} rows={4} placeholder="Freitext..." />
	</fieldset>

	<!-- Tags -->
	<fieldset class="space-y-2">
		<legend class="text-sm font-bold text-[var(--color-text-primary)] uppercase tracking-wider border-b border-[var(--color-surface-600)] pb-1 mb-2">Tags</legend>
		<div class="flex flex-wrap gap-1 mb-2">
			{#each tags as tag}
				<Tag text={tag} removable onremove={() => removeTag(tag)} />
			{/each}
		</div>
		<div class="flex gap-2">
			<input bind:value={newTag} placeholder="Neuer Tag..."
				onkeydown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addTag(); } }}
				class="flex-1 bg-[var(--color-surface-700)] border border-[var(--color-surface-500)] text-[var(--color-text-primary)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)]"
			/>
			<Button variant="secondary" size="sm" onclick={addTag}>+</Button>
		</div>
	</fieldset>

	<div class="flex justify-end gap-3 pt-4 border-t border-[var(--color-surface-600)]">
		<Button variant="secondary" onclick={() => history.back()}>Abbrechen</Button>
		<Button type="submit">{submitLabel}</Button>
	</div>
</form>
