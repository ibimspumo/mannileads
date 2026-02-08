<script lang="ts">
	interface Props {
		value?: string;
		label?: string;
		options: { value: string; label: string }[];
		onchange?: (e: Event) => void;
	}
	let { value = $bindable(''), label = '', options, onchange }: Props = $props();
</script>

{#if label}
	<label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">{label}</label>
{/if}
<select
	bind:value
	{onchange}
	class="w-full bg-[var(--color-surface-700)] border border-[var(--color-surface-500)] text-[var(--color-text-primary)] rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-[var(--color-accent)] cursor-pointer"
>
	{#each options as opt}
		<option value={opt.value}>{opt.label}</option>
	{/each}
</select>
