<script lang="ts">
	import Button from '$lib/components/atoms/Button.svelte';
	import { leads } from '$lib/stores/leads';
	import { parseCSVImport, parseJSONImport } from '$lib/utils/export';
	import { goto } from '$app/navigation';

	let fileContent = $state('');
	let format = $state<'json' | 'csv'>('json');
	let message = $state('');
	let error = $state('');

	function handleFile(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		format = file.name.endsWith('.csv') ? 'csv' : 'json';
		const reader = new FileReader();
		reader.onload = () => { fileContent = reader.result as string; };
		reader.readAsText(file);
	}

	function doImport() {
		error = '';
		message = '';
		const parsed = format === 'csv' ? parseCSVImport(fileContent) : parseJSONImport(fileContent);
		if (parsed.length === 0) {
			error = 'Keine Leads gefunden. Prüfe das Format.';
			return;
		}
		const ids = leads.importLeads(parsed);
		message = `${ids.length} Leads importiert!`;
	}

	function restoreBackup() {
		error = '';
		message = '';
		try {
			const parsed = JSON.parse(fileContent);
			if (!Array.isArray(parsed)) { error = 'Ungültiges Backup-Format'; return; }
			leads.replaceAll(parsed);
			message = `Backup wiederhergestellt: ${parsed.length} Leads`;
		} catch {
			error = 'JSON-Parse-Fehler';
		}
	}
</script>

<svelte:head>
	<title>Import — ManniLeads</title>
</svelte:head>

<div class="max-w-2xl space-y-6">
	<h1 class="text-xl font-bold text-[var(--color-text-primary)]">Import / Restore</h1>

	<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-6 space-y-4">
		<div>
			<label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-2 uppercase tracking-wider">Datei wählen (CSV oder JSON)</label>
			<input type="file" accept=".csv,.json" onchange={handleFile}
				class="text-sm text-[var(--color-text-secondary)] file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-[var(--color-surface-600)] file:text-[var(--color-text-primary)] file:cursor-pointer hover:file:bg-[var(--color-surface-500)]"
			/>
		</div>

		{#if fileContent}
			<div class="bg-[var(--color-surface-700)] rounded p-3 text-xs font-mono text-[var(--color-text-muted)] max-h-40 overflow-auto">
				{fileContent.slice(0, 500)}{fileContent.length > 500 ? '...' : ''}
			</div>

			<div class="flex gap-3">
				<Button onclick={doImport}>Leads importieren (hinzufügen)</Button>
				<Button variant="danger" onclick={restoreBackup}>Backup wiederherstellen (ersetzt alles!)</Button>
			</div>
		{/if}

		{#if message}
			<p class="text-sm text-green-400">{message}</p>
		{/if}
		{#if error}
			<p class="text-sm text-red-400">{error}</p>
		{/if}
	</div>

	<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-6">
		<h3 class="text-sm font-bold text-[var(--color-text-primary)] mb-3">CSV-Format</h3>
		<pre class="text-xs font-mono text-[var(--color-text-muted)] bg-[var(--color-surface-700)] rounded p-3 overflow-x-auto">Firma,Website,Branche,Größe,PLZ,Ort,Ansprechpartner,Position,Email,Telefon,Notizen
"Müller GmbH","https://mueller.de","Handwerk","5-10","19053","Schwerin","Max Müller","GF","max@mueller.de","+49123456",""</pre>
	</div>
</div>
