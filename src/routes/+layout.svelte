<script lang="ts">
	import '../app.css';
	import { auth } from '$lib/stores/auth';
	import { leads } from '$lib/stores/leads';
	import { exportJSON, downloadFile } from '$lib/utils/export';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	const isLogin = $derived($page.url.pathname === '/login');
	const isAuthed = $derived($auth);

	// Redirect to login if not authed
	$effect(() => {
		if (browser && !isAuthed && !isLogin) {
			goto('/login');
		}
	});

	async function backup() {
		const data = exportJSON($leads);
		const date = new Date().toISOString().slice(0, 10);
		downloadFile(data, `mannileads-backup-${date}.json`, 'application/json');
	}

	async function refresh() {
		await leads.load();
	}

	const navItems = [
		{ href: '/', label: 'Dashboard', icon: '▦' },
		{ href: '/leads', label: 'Leads', icon: '☰' },
		{ href: '/leads/new', label: '+ Neu', icon: '' },
		{ href: '/import', label: 'Import', icon: '↑' }
	];

	let mobileMenuOpen = $state(false);
</script>

{#if isLogin || !isAuthed}
	{@render children()}
{:else}
	<div class="min-h-screen flex flex-col">
		<!-- Top Bar -->
		<header class="bg-[var(--color-surface-800)] border-b border-[var(--color-surface-600)] px-4 py-2.5 flex items-center justify-between sticky top-0 z-50 backdrop-blur-sm bg-opacity-95">
			<div class="flex items-center gap-8">
				<a href="/" class="flex items-center gap-2 group">
					<span class="text-lg font-bold text-[var(--color-accent)] tracking-tight font-mono group-hover:drop-shadow-[0_0_8px_rgba(255,165,2,0.4)] transition-all">ML</span>
					<span class="text-sm font-medium text-[var(--color-text-secondary)] hidden sm:inline">ManniLeads</span>
				</a>
				<nav class="hidden md:flex items-center gap-0.5">
					{#each navItems as item}
						<a href={item.href}
							class="px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200
								{$page.url.pathname === item.href
									? 'bg-[var(--color-accent)] text-[var(--color-surface-900)] font-semibold shadow-[inset_0_0_0_1px_rgba(255,165,2,0.3)]'
									: 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-700)]'}"
						>
							{item.label}
						</a>
					{/each}
				</nav>
			</div>
			<div class="flex items-center gap-2">
				<button onclick={refresh}
					class="px-2.5 py-1.5 text-xs font-medium text-[var(--color-text-muted)] hover:text-[var(--color-accent)] rounded-md transition-colors cursor-pointer hover:bg-[var(--color-surface-700)]"
					title="Daten aktualisieren"
				>↻</button>
				<button onclick={backup}
					class="px-2.5 py-1.5 text-xs font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] rounded-md transition-colors cursor-pointer hover:bg-[var(--color-surface-700)]"
				>💾</button>
				<button onclick={() => auth.logout()}
					class="px-2.5 py-1.5 text-xs text-[var(--color-text-muted)] hover:text-red-400 rounded-md transition-colors cursor-pointer hover:bg-[var(--color-surface-700)]"
				>⏻</button>
			</div>
		</header>

		<!-- Mobile Nav -->
		<nav class="md:hidden flex items-center gap-0.5 px-3 py-2 bg-[var(--color-surface-800)] border-b border-[var(--color-surface-600)] overflow-x-auto">
			{#each navItems as item}
				<a href={item.href}
					class="px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-all
						{$page.url.pathname === item.href
							? 'bg-[var(--color-accent)] text-[var(--color-surface-900)] font-semibold'
							: 'text-[var(--color-text-secondary)]'}"
				>
					{item.label}
				</a>
			{/each}
		</nav>

		<!-- Content -->
		<main class="flex-1 p-4 md:p-6 max-w-7xl mx-auto w-full">
			{@render children()}
		</main>

		<!-- Footer -->
		<footer class="border-t border-[var(--color-surface-700)] px-4 py-2 text-center">
			<span class="text-[10px] font-mono text-[var(--color-text-muted)] tracking-wider">MANNILEADS v2 · CONVEX · AGENTZ</span>
		</footer>
	</div>
{/if}
