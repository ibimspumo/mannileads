<script lang="ts">
	interface Props {
		label: string;
		value: string | number;
		color?: string;
	}
	let { label, value, color = 'var(--color-text-primary)' }: Props = $props();
</script>

<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg p-4">
	<div class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1">{label}</div>
	<div class="text-2xl font-bold tabular-nums" style="color: {color}">{value}</div>
</div>
