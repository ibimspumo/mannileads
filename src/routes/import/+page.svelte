<script lang="ts">
	import Button from '$lib/components/atoms/Button.svelte';
	import { leads } from '$lib/stores/leads';
	import { parseCSVImport, parseJSONImport } from '$lib/utils/export';
	import { goto } from '$app/navigation';

	let fileContent = $state('');
	let format = $state<'json' | 'csv'>('json');
	let message = $state('');
	let error = $state('');
	let importing = $state(false);

	function handleFile(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		format = file.name.endsWith('.csv') ? 'csv' : 'json';
		const reader = new FileReader();
		reader.onload = () => { fileContent = reader.result as string; };
		reader.readAsText(file);
	}

	async function doImport() {
		error = '';
		message = '';
		importing = true;
		try {
			const parsed = format === 'csv' ? parseCSVImport(fileContent) : parseJSONImport(fileContent);
			if (parsed.length === 0) {
				error = 'Keine Leads gefunden. Prüfe das Format.';
				return;
			}
			const ids = await leads.importLeads(parsed);
			message = `${ids.length} Leads importiert!`;
		} catch (e: any) {
			error = `Fehler: ${e.message ?? e}`;
		} finally {
			importing = false;
		}
	}

	async function restoreBackup() {
		error = '';
		message = '';
		importing = true;
		try {
			const parsed = JSON.parse(fileContent);
			if (!Array.isArray(parsed)) { error = 'Ungültiges Backup-Format'; return; }
			await leads.replaceAll(parsed);
			message = `Backup wiederhergestellt: ${parsed.length} Leads`;
		} catch {
			error = 'JSON-Parse-Fehler';
		} finally {
			importing = false;
		}
	}
</script>

<svelte:head>
	<title>Import — ManniLeads</title>
</svelte:head>

<div class="max-w-2xl space-y-6 animate-fade-in">
	<h1 class="text-xl font-bold text-[var(--color-text-primary)]">Import / Restore</h1>

	<div class="panel p-6 space-y-4">
		<div>
			<label class="block text-[10px] font-bold text-[var(--color-text-muted)] mb-2 uppercase tracking-widest">Datei wählen (CSV oder JSON)</label>
			<input type="file" accept=".csv,.json" onchange={handleFile}
				class="text-sm text-[var(--color-text-secondary)] file:mr-4 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-[var(--color-surface-600)] file:text-[var(--color-text-primary)] file:cursor-pointer hover:file:bg-[var(--color-surface-500)]"
			/>
		</div>

		{#if fileContent}
			<div class="bg-[var(--color-surface-700)] rounded p-3 text-[10px] font-mono text-[var(--color-text-muted)] max-h-40 overflow-auto leading-relaxed">
				{fileContent.slice(0, 500)}{fileContent.length > 500 ? '...' : ''}
			</div>

			{#if importing}
				<div class="text-center py-4">
					<div class="text-xl animate-pulse-hot mb-2">◈</div>
					<p class="text-xs text-[var(--color-text-secondary)]">Wird verarbeitet...</p>
				</div>
			{:else}
				<div class="flex gap-3">
					<Button onclick={doImport}>Leads importieren</Button>
					<Button variant="danger" onclick={restoreBackup}>Backup wiederherstellen</Button>
				</div>
			{/if}
		{/if}

		{#if message}
			<div class="flex items-center gap-2 p-3 rounded bg-[var(--color-success)] bg-opacity-10 border border-[var(--color-success)] border-opacity-20">
				<span class="text-[var(--color-success)]">✓</span>
				<p class="text-sm text-[var(--color-success)]">{message}</p>
			</div>
		{/if}
		{#if error}
			<div class="flex items-center gap-2 p-3 rounded bg-[var(--color-error)] bg-opacity-10 border border-[var(--color-error)] border-opacity-20">
				<span class="text-[var(--color-error)]">✗</span>
				<p class="text-sm text-[var(--color-error)]">{error}</p>
			</div>
		{/if}
	</div>

	<div class="panel p-6">
		<h3 class="text-xs font-bold text-[var(--color-text-primary)] mb-3">CSV-Format</h3>
		<pre class="text-[10px] font-mono text-[var(--color-text-muted)] bg-[var(--color-surface-700)] rounded p-3 overflow-x-auto leading-relaxed">Firma,Website,Branche,Größe,PLZ,Ort,Ansprechpartner,Position,Email,Telefon,Notizen
"Müller GmbH","https://mueller.de","Handwerk","5-10","19053","Schwerin","Max Müller","GF","max@mueller.de","+49123456",""</pre>
	</div>
</div>
