import App from './App.svelte';
import './styles/theme.css';

const target = document.getElementById('app');
if (!target) {
  throw new Error('Root element #app not found. Check index.html.');
}

const app = new App({ target });

export default app;
