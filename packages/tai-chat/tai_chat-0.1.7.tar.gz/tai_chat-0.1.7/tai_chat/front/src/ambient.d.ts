// Svelte 5 runes global declarations
declare global {
  // Svelte 5 runes - these should be globally available
  var $state: <T>(initial?: T) => T;
  var $derived: <T>(fn: () => T) => T;
  var $effect: (fn: () => void | (() => void)) => void;
  var $props: <T extends Record<string, any> = Record<string, any>>() => T;
  var $bindable: <T>(value?: T) => T;
  var $inspect: (...values: any[]) => void;
}

export {};