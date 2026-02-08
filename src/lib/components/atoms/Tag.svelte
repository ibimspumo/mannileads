<script lang="ts">
	interface Props {
		text: string;
		removable?: boolean;
		onremove?: () => void;
	}
	let { text, removable = false, onremove }: Props = $props();
</script>

<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] text-xs">
	{text}
	{#if removable}
		<button class="hover:text-[var(--color-text-primary)] cursor-pointer" onclick={onremove}>×</button>
	{/if}
</span>
