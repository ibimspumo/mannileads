<script lang="ts">
	interface Props {
		value?: string;
		placeholder?: string;
		label?: string;
		rows?: number;
	}
	let { value = $bindable(''), placeholder = '', label = '', rows = 3 }: Props = $props();
</script>

{#if label}
	<label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">{label}</label>
{/if}
<textarea
	{placeholder}
	{rows}
	bind:value
	class="w-full bg-[var(--color-surface-700)] border border-[var(--color-surface-500)] text-[var(--color-text-primary)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] placeholder:text-[var(--color-text-muted)] resize-y"
></textarea>
