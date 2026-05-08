self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('academia-cache').then((cache) => {
      return cache.addAll([
        '/',
        '/assets/logo_academia.png',
        '/assets/manifest.json',
        '/bitacora',
        '/finanzas',
        '/backtesting'
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
