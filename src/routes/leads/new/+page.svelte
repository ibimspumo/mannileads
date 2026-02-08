<script lang="ts">
	import LeadForm from '$lib/components/organisms/LeadForm.svelte';
	import { leads } from '$lib/stores/leads';
	import { goto } from '$app/navigation';
	import type { Lead } from '$lib/types/lead';

	function handleSubmit(data: Partial<Lead>) {
		const id = leads.add(data);
		goto(`/leads/${id}`);
	}
</script>

<svelte:head>
	<title>Neuer Lead — ManniLeads</title>
</svelte:head>

<div class="max-w-3xl">
	<h1 class="text-xl font-bold text-[var(--color-text-primary)] mb-6">Neuer Lead</h1>
	<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-6">
		<LeadForm onsubmit={handleSubmit} submitLabel="Lead anlegen" />
	</div>
</div>
