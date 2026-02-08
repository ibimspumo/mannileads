<script lang="ts">
	import { auth } from '$lib/stores/auth';
	import { goto } from '$app/navigation';
	import Button from '$lib/components/atoms/Button.svelte';
	import Input from '$lib/components/atoms/Input.svelte';

	let password = $state('');
	let error = $state('');

	let loading = $state(false);

	async function handleLogin(e: SubmitEvent) {
		e.preventDefault();
		loading = true;
		error = '';
		const ok = await auth.login(password);
		loading = false;
		if (ok) {
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

<div class="min-h-screen flex items-center justify-center bg-[var(--color-surface-900)] relative overflow-hidden">
	<!-- Subtle grid background -->
	<div class="absolute inset-0 opacity-[0.03]" style="background-image: linear-gradient(var(--color-text-primary) 1px, transparent 1px), linear-gradient(90deg, var(--color-text-primary) 1px, transparent 1px); background-size: 40px 40px;"></div>

	<div class="w-full max-w-sm p-6 relative z-10 animate-fade-in">
		<div class="text-center mb-10">
			<div class="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-[var(--color-accent)] bg-opacity-10 border border-[var(--color-accent)] border-opacity-20 mb-4">
				<span class="text-2xl font-bold font-mono text-[var(--color-accent)]">ML</span>
			</div>
			<h1 class="text-xl font-bold text-[var(--color-text-primary)] tracking-tight">ManniLeads</h1>
			<p class="text-xs text-[var(--color-text-muted)] mt-1 uppercase tracking-widest">Lead-Generierung · AgentZ</p>
		</div>
		<form onsubmit={handleLogin} class="space-y-4">
			<Input type="password" bind:value={password} placeholder="Passwort eingeben..." required />
			{#if error}
				<div class="flex items-center gap-2 text-xs text-[var(--color-error)]">
					<span>✗</span> {error}
				</div>
			{/if}
			<Button type="submit" size="lg">Einloggen</Button>
		</form>
		<p class="text-center text-[10px] text-[var(--color-text-muted)] mt-8 font-mono tracking-wider">v2 · CONVEX</p>
	</div>
</div>
