<script lang="ts">
	let {
		options = [],
		value = $bindable(''),
		label = '',
		placeholder = '— Alle —',
		onchange = () => {}
	}: {
		options: string[];
		value: string;
		label: string;
		placeholder?: string;
		onchange?: () => void;
	} = $props();

	let search = $state('');
	let open = $state(false);
	let inputEl: HTMLInputElement | undefined = $state();

	let filtered = $derived(
		search
			? options.filter((o) => o.toLowerCase().includes(search.toLowerCase()))
			: options
	);

	let displayValue = $derived(value || '');

	function select(val: string) {
		value = val;
		search = '';
		open = false;
		onchange();
	}

	function clear() {
		value = '';
		search = '';
		open = false;
		onchange();
	}

	function handleFocus() {
		open = true;
		search = '';
	}

	function handleBlur(e: FocusEvent) {
		// Delay to allow click on dropdown item
		setTimeout(() => {
			open = false;
			search = '';
		}, 200);
	}

	function handleInput(e: Event) {
		search = (e.target as HTMLInputElement).value;
		open = true;
	}
</script>

<div class="relative">
	{#if label}
		<label class="block text-xs font-mono font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-1">
			{label}
		</label>
	{/if}
	<div class="relative">
		<input
			bind:this={inputEl}
			type="text"
			value={open ? search : displayValue}
			placeholder={placeholder}
			onfocus={handleFocus}
			onblur={handleBlur}
			oninput={handleInput}
			class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none transition-colors pr-8"
		/>
		{#if value}
			<button
				type="button"
				onclick={clear}
				class="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-accent)] text-xs"
				title="Filter löschen"
			>✕</button>
		{/if}
	</div>
	{#if open && filtered.length > 0}
		<div class="absolute z-50 w-full mt-1 max-h-48 overflow-y-auto bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded shadow-lg">
			<button
				type="button"
				onmousedown={(e) => { e.preventDefault(); clear(); }}
				class="w-full text-left px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface-600)] transition-colors italic"
			>
				— Alle —
			</button>
			{#each filtered.slice(0, 50) as option}
				<button
					type="button"
					onmousedown={(e) => { e.preventDefault(); select(option); }}
					class="w-full text-left px-3 py-1.5 text-sm text-[var(--color-text-primary)] hover:bg-[var(--color-surface-600)] transition-colors"
					class:bg-[var(--color-surface-600)]={option === value}
				>
					{option}
				</button>
			{/each}
			{#if filtered.length > 50}
				<div class="px-3 py-1.5 text-xs text-[var(--color-text-muted)]">
					+ {filtered.length - 50} weitere...
				</div>
			{/if}
		</div>
	{/if}
</div>
