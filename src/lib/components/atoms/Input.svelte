<script lang="ts">
	interface Props {
		value?: string;
		placeholder?: string;
		type?: string;
		label?: string;
		name?: string;
		required?: boolean;
		disabled?: boolean;
		oninput?: (e: Event) => void;
		onchange?: (e: Event) => void;
	}
	let { value = $bindable(''), placeholder = '', type = 'text', label = '', name = '', required = false, disabled = false, oninput, onchange }: Props = $props();
</script>

{#if label}
	<label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">{label}</label>
{/if}
<input
	{type}
	{name}
	{placeholder}
	{required}
	{disabled}
	bind:value
	{oninput}
	{onchange}
	class="w-full bg-[var(--color-surface-700)] border border-[var(--color-surface-500)] text-[var(--color-text-primary)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] focus:border-[var(--color-accent)] placeholder:text-[var(--color-text-muted)] disabled:opacity-40"
/>
