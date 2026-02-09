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
		{ href: '/', label: 'Dashboard' },
		{ href: '/leads', label: 'Leads' },
		{ href: '/leads/new', label: '+ Neu' },
		{ href: '/import', label: 'Import' },
		{ href: '/coverage', label: 'Coverage' }
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
			<div class="flex items-center gap-1">
				<button onclick={refresh}
					class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-[var(--color-text-muted)] hover:text-[var(--color-accent)] rounded-md transition-colors cursor-pointer hover:bg-[var(--color-surface-700)]"
					title="Daten neu laden"
				>
					<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h5M20 20v-5h-5M5.1 15A7 7 0 0119.8 13M18.9 9A7 7 0 005.2 11" /></svg>
					<span class="hidden sm:inline">Aktualisieren</span>
				</button>
				<button onclick={backup}
					class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] rounded-md transition-colors cursor-pointer hover:bg-[var(--color-surface-700)]"
					title="Backup als JSON herunterladen"
				>
					<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3M3 17v2a2 2 0 002 2h14a2 2 0 002-2v-2" /></svg>
					<span class="hidden sm:inline">Backup</span>
				</button>
				<button onclick={() => auth.logout()}
					class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-[var(--color-text-muted)] hover:text-red-400 rounded-md transition-colors cursor-pointer hover:bg-[var(--color-surface-700)]"
					title="Abmelden"
				>
					<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2h5a2 2 0 012 2v1" /></svg>
					<span class="hidden sm:inline">Abmelden</span>
				</button>
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
