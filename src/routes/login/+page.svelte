<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import Button from '$lib/components/atoms/Button.svelte';
	import Input from '$lib/components/atoms/Input.svelte';

	let password = $state('');
	let error = $state('');

	function handleLogin(e: SubmitEvent) {
		e.preventDefault();
		if (auth.login(password)) {
			goto('/');
		} else {
			error = 'Falsches Passwort';
			password = '';
		}
	}
</script>

<svelte:head>
	<title>Login — ManniLeads</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-[var(--color-surface-900)]">
	<div class="w-full max-w-sm p-6">
		<div class="text-center mb-8">
			<h1 class="text-2xl font-bold text-[var(--color-accent)] font-mono tracking-tight">ManniLeads</h1>
			<p class="text-sm text-[var(--color-text-muted)] mt-1">Lead-Generierung für AgentZ</p>
		</div>
		<form onsubmit={handleLogin} class="space-y-4">
			<Input type="password" bind:value={password} placeholder="Passwort" required />
			{#if error}
				<p class="text-xs text-red-400">{error}</p>
			{/if}
			<Button type="submit" size="lg">Einloggen</Button>
		</form>
	</div>
</div>
