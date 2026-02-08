<script lang="ts">
	interface Props {
		label: string;
		value: string | number;
		color?: string;
		icon?: string;
		pulse?: boolean;
	}
	let { label, value, color = 'var(--color-text-primary)', icon = '', pulse = false }: Props = $props();
</script>

<div class="panel p-4 hover:border-[var(--color-surface-500)] transition-colors group">
	<div class="flex items-center justify-between mb-2">
		<span class="text-[10px] font-bold text-[var(--color-text-muted)] uppercase tracking-widest">{label}</span>
		{#if icon}
			<span class="text-sm opacity-30 group-hover:opacity-50 transition-opacity" style="color: {color}">{icon}</span>
		{/if}
	</div>
	<div class="text-2xl font-bold tabular-nums font-mono {pulse ? 'animate-pulse-hot' : ''}" style="color: {color}">{value}</div>
</div>
