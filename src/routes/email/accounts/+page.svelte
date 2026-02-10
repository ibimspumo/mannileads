<script lang="ts">
	import { onMount } from 'svelte';
	import { ConvexHttpClient } from 'convex/browser';
	import { PUBLIC_CONVEX_URL } from '$env/static/public';
	import { api } from '$lib/convex/_generated/api';

	const client = new ConvexHttpClient(PUBLIC_CONVEX_URL);

	let accounts = $state<any[]>([]);
	let loading = $state(true);
	let showForm = $state(false);
	let editingId = $state<string | null>(null);

	// Form state
	let form = $state({
		name: '',
		fromEmail: '',
		fromName: '',
		signatureHtml: '',
		sesAccessKey: '',
		sesSecretKey: '',
		sesRegion: 'us-east-1'
	});

	onMount(async () => {
		await loadAccounts();
	});

	async function loadAccounts() {
		try {
			accounts = await client.query(api.email.listAccounts);
		} catch (error) {
			console.error('Failed to load accounts:', error);
		} finally {
			loading = false;
		}
	}

	function resetForm() {
		form = {
			name: '',
			fromEmail: '',
			fromName: '',
			signatureHtml: '',
			sesAccessKey: '',
			sesSecretKey: '',
			sesRegion: 'us-east-1'
		};
		editingId = null;
		showForm = false;
	}

	function editAccount(account: any) {
		form = {
			name: account.name,
			fromEmail: account.fromEmail,
			fromName: account.fromName,
			signatureHtml: account.signatureHtml,
			sesAccessKey: account.sesAccessKey,
			sesSecretKey: account.sesSecretKey,
			sesRegion: account.sesRegion
		};
		editingId = account._id;
		showForm = true;
	}

	async function saveAccount() {
		try {
			if (editingId) {
				await client.mutation(api.email.updateAccount, {
					id: editingId as any,
					...form
				});
			} else {
				await client.mutation(api.email.createAccount, form);
			}
			await loadAccounts();
			resetForm();
		} catch (error) {
			console.error('Failed to save account:', error);
			alert('Fehler beim Speichern: ' + error);
		}
	}

	async function deleteAccount(id: string) {
		if (!confirm('Account wirklich löschen?')) return;
		try {
			await client.mutation(api.email.deleteAccount, { id: id as any });
			await loadAccounts();
		} catch (error) {
			console.error('Failed to delete account:', error);
			alert('Fehler beim Löschen: ' + error);
		}
	}

	async function toggleActive(id: string, active: boolean) {
		try {
			await client.mutation(api.email.updateAccount, {
				id: id as any,
				active: !active
			});
			await loadAccounts();
		} catch (error) {
			console.error('Failed to toggle active:', error);
		}
	}
</script>

<div class="space-y-6 animate-fade-in">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold font-mono tracking-tight text-[var(--color-accent)]">
				EMAIL ACCOUNTS
			</h1>
			<p class="text-sm text-[var(--color-text-muted)] mt-1">
				AWS SES Multi-Account Configuration
			</p>
		</div>
		<div class="flex gap-2">
			<a
				href="/email"
				class="px-3 py-1.5 text-xs font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded transition-all"
			>
				← ZURÜCK
			</a>
			<button
				onclick={() => (showForm = !showForm)}
				class="px-3 py-1.5 text-xs font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded transition-all shadow-[0_0_12px_rgba(255,165,2,0.3)]"
			>
				{showForm ? 'ABBRECHEN' : '+ NEUER ACCOUNT'}
			</button>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="skeleton w-32 h-32"></div>
		</div>
	{:else}
		<!-- Form -->
		{#if showForm}
			<div class="panel animate-fade-in">
				<div class="panel-header">{editingId ? 'Account bearbeiten' : 'Neuer Account'}</div>
				<div class="p-4 space-y-4">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								Account Name
							</label>
							<input
								type="text"
								bind:value={form.name}
								placeholder="z.B. Schwerin ist Geil"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
						</div>
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								From Name
							</label>
							<input
								type="text"
								bind:value={form.fromName}
								placeholder="z.B. Manfred Bellmann"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
						</div>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								From Email
							</label>
							<input
								type="email"
								bind:value={form.fromEmail}
								placeholder="kontakt@schwerinistgeil.de"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
						</div>
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								SES Region
							</label>
							<select
								bind:value={form.sesRegion}
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							>
								<option value="us-east-1">us-east-1</option>
								<option value="eu-west-1">eu-west-1</option>
								<option value="eu-central-1">eu-central-1</option>
							</select>
						</div>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								AWS Access Key
							</label>
							<input
								type="text"
								bind:value={form.sesAccessKey}
								placeholder="AKIAIOSFODNN7EXAMPLE"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] font-mono focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
						</div>
						<div>
							<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
								AWS Secret Key
							</label>
							<input
								type="password"
								bind:value={form.sesSecretKey}
								placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
								class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] font-mono focus:border-[var(--color-accent)] focus:outline-none transition-colors"
							/>
						</div>
					</div>

					<div>
						<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
							HTML Signatur
						</label>
						<textarea
							bind:value={form.signatureHtml}
							rows="4"
							placeholder="<p>Mit freundlichen Grüßen<br>Manfred Bellmann</p>"
							class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] font-mono focus:border-[var(--color-accent)] focus:outline-none transition-colors"
						></textarea>
					</div>

					<div class="flex gap-2 pt-2">
						<button
							onclick={saveAccount}
							class="px-4 py-2 text-sm font-bold font-mono tracking-wide bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded transition-all"
						>
							{editingId ? 'AKTUALISIEREN' : 'ERSTELLEN'}
						</button>
						<button
							onclick={resetForm}
							class="px-4 py-2 text-sm font-medium font-mono tracking-wide bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] rounded transition-all"
						>
							ABBRECHEN
						</button>
					</div>
				</div>
			</div>
		{/if}

		<!-- Accounts List -->
		<div class="panel">
			<div class="panel-header">Accounts</div>
			<div class="divide-y divide-[var(--color-surface-700)]">
				{#if accounts.length === 0}
					<div class="p-8 text-center">
						<p class="text-sm text-[var(--color-text-muted)]">Keine Accounts konfiguriert.</p>
					</div>
				{:else}
					{#each accounts as account}
						<div class="p-4 hover:bg-[var(--color-surface-700)] transition-colors">
							<div class="flex items-start justify-between">
								<div class="flex-1">
									<div class="flex items-center gap-2 mb-1">
										<h3 class="font-bold text-[var(--color-text-primary)]">{account.name}</h3>
										<span
											class="inline-block px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider rounded {account.active
												? 'bg-[var(--color-success)] text-[var(--color-surface-900)]'
												: 'bg-[var(--color-surface-600)] text-[var(--color-text-muted)]'}"
										>
											{account.active ? 'AKTIV' : 'INAKTIV'}
										</span>
										{#if account.verified}
											<span
												class="inline-block px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider rounded bg-[var(--color-info)] text-[var(--color-surface-900)]"
											>
												VERIFIED
											</span>
										{/if}
									</div>
									<div class="text-sm text-[var(--color-text-secondary)] space-y-1">
										<div class="flex items-center gap-2">
											<span class="font-mono">{account.fromName}</span>
											<span class="text-[var(--color-text-muted)]">&lt;{account.fromEmail}&gt;</span>
										</div>
										<div class="text-xs text-[var(--color-text-muted)]">
											Region: {account.sesRegion} • Gesendet: {account.totalSent}
										</div>
									</div>
								</div>
								<div class="flex gap-1">
									<button
										onclick={() => toggleActive(account._id, account.active)}
										class="px-2 py-1 text-xs font-mono text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors"
									>
										{account.active ? 'DEAKTIVIEREN' : 'AKTIVIEREN'}
									</button>
									<button
										onclick={() => editAccount(account)}
										class="px-2 py-1 text-xs font-mono text-[var(--color-accent)] hover:underline"
									>
										BEARBEITEN
									</button>
									<button
										onclick={() => deleteAccount(account._id)}
										class="px-2 py-1 text-xs font-mono text-[var(--color-error)] hover:underline"
									>
										LÖSCHEN
									</button>
								</div>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>
	{/if}
</div>
