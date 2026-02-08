<script lang="ts">
	import LeadForm from '$lib/components/organisms/LeadForm.svelte';
	import { leads } from '$lib/stores/leads';
	import { goto } from '$app/navigation';
	import type { Lead } from '$lib/types/lead';

	let saving = $state(false);

	async function handleSubmit(data: Partial<Lead>) {
		saving = true;
		try {
			const id = await leads.add(data);
			goto(`/leads/${id}`);
		} catch (e) {
			console.error('Fehler beim Speichern:', e);
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Neuer Lead — ManniLeads</title>
</svelte:head>

<div class="max-w-3xl animate-fade-in">
	<h1 class="text-xl font-bold text-[var(--color-text-primary)] mb-6">Neuer Lead</h1>
	{#if saving}
		<div class="panel p-8 text-center">
			<div class="text-2xl mb-2 animate-pulse-hot">◈</div>
			<p class="text-sm text-[var(--color-text-secondary)]">Wird gespeichert...</p>
		</div>
	{:else}
		<div class="panel p-6">
			<LeadForm onsubmit={handleSubmit} submitLabel="Lead anlegen" />
		</div>
	{/if}
</div>
