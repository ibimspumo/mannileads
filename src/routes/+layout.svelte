<script lang="ts">
	import '../app.css';
	import { auth } from '$lib/stores/auth';
	import { leads } from '$lib/stores/leads';
	import { exportJSON, downloadFile } from '$lib/utils/export';
	import { page } from '$app/stores';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	const isLogin = $derived($page.url.pathname === '/login');
	const isAuthed = $derived($auth);

	function backup() {
		const data = exportJSON($leads);
		const date = new Date().toISOString().slice(0, 10);
		downloadFile(data, `mannileads-backup-${date}.json`, 'application/json');
	}

	const navItems = [
		{ href: '/', label: 'Dashboard', icon: '◻' },
		{ href: '/leads', label: 'Leads', icon: '☰' },
		{ href: '/leads/new', label: '+ Neu', icon: '' },
		{ href: '/import', label: 'Import', icon: '↑' }
	];
</script>

{#if !isAuthed && !isLogin}
	<script>
		window.location.href = '/login';
	</script>
{:else if isLogin}
	{@render children()}
{:else}
	<div class="min-h-screen flex flex-col">
		<!-- Top Bar -->
		<header class="bg-[var(--color-surface-800)] border-b border-[var(--color-surface-600)] px-4 py-2 flex items-center justify-between">
			<div class="flex items-center gap-6">
				<a href="/" class="text-lg font-bold text-[var(--color-accent)] tracking-tight font-mono">ManniLeads</a>
				<nav class="hidden md:flex items-center gap-1">
					{#each navItems as item}
						<a href={item.href}
							class="px-3 py-1.5 rounded-md text-sm transition-colors {$page.url.pathname === item.href ? 'bg-[var(--color-surface-600)] text-[var(--color-text-primary)]' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-700)]'}"
						>
							{item.label}
						</a>
					{/each}
				</nav>
			</div>
			<div class="flex items-center gap-2">
				<button onclick={backup}
					class="px-3 py-1.5 text-xs font-medium bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded-md transition-colors cursor-pointer"
				>
					💾 Backup
				</button>
				<button onclick={() => auth.logout()}
					class="px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:text-red-400 rounded-md transition-colors cursor-pointer"
				>
					Logout
				</button>
			</div>
		</header>

		<!-- Mobile Nav -->
		<nav class="md:hidden flex items-center gap-1 px-4 py-2 bg-[var(--color-surface-800)] border-b border-[var(--color-surface-600)] overflow-x-auto">
			{#each navItems as item}
				<a href={item.href}
					class="px-3 py-1 rounded text-xs whitespace-nowrap {$page.url.pathname === item.href ? 'bg-[var(--color-surface-600)] text-[var(--color-text-primary)]' : 'text-[var(--color-text-secondary)]'}"
				>
					{item.label}
				</a>
			{/each}
		</nav>

		<!-- Content -->
		<main class="flex-1 p-4 md:p-6 max-w-7xl mx-auto w-full">
			{@render children()}
		</main>
	</div>
{/if}
