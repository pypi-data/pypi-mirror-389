import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const allowedHosts = process.env.VITE_ALLOWED_HOSTS?.split(',') || ['localhost'];

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	preview: {
		allowedHosts
	}
});
