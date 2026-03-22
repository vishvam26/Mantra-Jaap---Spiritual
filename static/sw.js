const CACHE_NAME = 'mantra-jaap-v1';
const urlsToCache = [
  '/',
  '/auto-jap.html',
  '/static/logo.png',
  '/static/audio/bansuri_bg.mp3',
  '/static/audio/auto.mp3',
  '/static/audio/radhe.mp3',
  '/static/audio/shivay.mp3',
  '/static/audio/ram.mp3',
  '/static/audio/krishna.mp3'
];

// Install Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('Opened cache');
      return cache.addAll(urlsToCache);
    })
  );
});

// Fetch Assets from Cache
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      // Jo request cache ma hoy to tya thi apo, nahi to network par jao
      return response || fetch(event.request);
    })
  );
});

// Activate & Cleanup Old Caches
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
