<script lang="ts">
	interface Props {
		variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
		size?: 'sm' | 'md' | 'lg';
		disabled?: boolean;
		type?: 'button' | 'submit';
		onclick?: (e: MouseEvent) => void;
		children: import('svelte').Snippet;
	}
	let { variant = 'primary', size = 'md', disabled = false, type = 'button', onclick, children }: Props = $props();

	const base = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[var(--color-surface-900)] disabled:opacity-40 disabled:pointer-events-none cursor-pointer';
	const variants: Record<string, string> = {
		primary: 'bg-[var(--color-accent)] text-black hover:bg-amber-400 focus:ring-amber-500',
		secondary: 'bg-[var(--color-surface-600)] text-[var(--color-text-primary)] hover:bg-[var(--color-surface-500)] focus:ring-[var(--color-surface-400)]',
		danger: 'bg-red-600 text-white hover:bg-red-500 focus:ring-red-500',
		ghost: 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-700)] focus:ring-[var(--color-surface-400)]'
	};
	const sizes: Record<string, string> = {
		sm: 'text-xs px-2 py-1 rounded',
		md: 'text-sm px-3 py-1.5 rounded-md',
		lg: 'text-base px-4 py-2 rounded-md'
	};
</script>

<button {type} {disabled} class="{base} {variants[variant]} {sizes[size]}" {onclick}>
	{@render children()}
</button>
