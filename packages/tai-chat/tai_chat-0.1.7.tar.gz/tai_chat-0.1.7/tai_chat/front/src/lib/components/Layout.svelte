<script lang="ts">
  import { onMount } from 'svelte';
  import type { Snippet } from 'svelte';
  import { themeActions } from '../stores';
  import { authService } from '../auth';

  interface Props {
    children: Snippet;
  }

  let { children }: Props = $props();

  onMount(async () => {
    // Initialize all stores
    await authService.initialize();
    themeActions.init();
  });
</script>

<div class="min-h-screen bg-background text-text transition-colors duration-200">
  {@render children()}
</div>

<style>
  /* Custom CSS variables that will be set by the theme store */
  :global(:root) {
    --color-primary: #3b82f6;
    --color-secondary: #6b7280;
    --color-accent: #10b981;
    --color-background: #ffffff;
    --color-surface: #f9fafb;
    --color-text: #111827;
    --color-text-secondary: #6b7280;
    --color-border: #e5e7eb;
    --color-success: #10b981;
    --color-warning: #f59e0b;
    --color-error: #ef4444;
  }

  :global(.bg-background) {
    background-color: var(--color-background);
  }

  :global(.bg-surface) {
    background-color: var(--color-surface);
  }

  :global(.bg-primary) {
    background-color: var(--color-primary);
  }

  :global(.bg-secondary) {
    background-color: var(--color-secondary);
  }

  :global(.bg-accent) {
    background-color: var(--color-accent);
  }

  :global(.text-text) {
    color: var(--color-text);
  }

  :global(.text-text-secondary) {
    color: var(--color-text-secondary);
  }

  :global(.text-primary) {
    color: var(--color-primary);
  }

  :global(.text-accent) {
    color: var(--color-accent);
  }

  :global(.border-border) {
    border-color: var(--color-border);
  }

  :global(.text-success) {
    color: var(--color-success);
  }

  :global(.text-warning) {
    color: var(--color-warning);
  }

  :global(.text-error) {
    color: var(--color-error);
  }

  :global(.bg-success) {
    background-color: var(--color-success);
  }

  :global(.bg-warning) {
    background-color: var(--color-warning);
  }

  :global(.bg-error) {
    background-color: var(--color-error);
  }
</style>
