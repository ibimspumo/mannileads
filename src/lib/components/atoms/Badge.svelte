<script lang="ts">
	interface Props {
		color?: string;
		children: import('svelte').Snippet;
	}
	let { color = 'var(--color-surface-400)', children }: Props = $props();
</script>

<span
	class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
	style="background: {color}20; color: {color}; border: 1px solid {color}40;"
>
	{@render children()}
</span>
