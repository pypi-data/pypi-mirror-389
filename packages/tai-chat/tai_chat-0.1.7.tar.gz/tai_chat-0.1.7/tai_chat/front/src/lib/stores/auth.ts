// Re-export the new auth store and functionality
export { auth } from '../auth/authStore';

// For backward compatibility, create some derived stores
import { derived } from 'svelte/store';
import { auth } from '../auth/authStore';

export const authStore = derived(auth, $auth => ({
  isAuthenticated: $auth.state === 'authenticated',
  user: $auth.user,
  token: $auth.token
}));
