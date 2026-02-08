<script lang="ts">
	interface Props {
		value?: string;
		placeholder?: string;
		oninput?: (e: Event) => void;
	}
	let { value = $bindable(''), placeholder = 'Suchen...', oninput }: Props = $props();
</script>

<div class="relative">
	<span class="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]">⌕</span>
	<input
		type="search"
		{placeholder}
		bind:value
		{oninput}
		class="w-full bg-[var(--color-surface-700)] border border-[var(--color-surface-500)] text-[var(--color-text-primary)] rounded-md pl-9 pr-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] placeholder:text-[var(--color-text-muted)]"
	/>
</div>
