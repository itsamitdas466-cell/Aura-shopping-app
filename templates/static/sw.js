const CACHE='aura-shell-v1';
self.addEventListener('install', event => { self.skipWaiting(); event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(['/static/style.css','/static/icon.svg','/static/manifest.webmanifest']))); });
self.addEventListener('activate', event => { event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', event => { if (event.request.method !== 'GET') return; const url = new URL(event.request.url); if (url.origin === self.location.origin && url.pathname.startsWith('/static/')) event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request))); });
