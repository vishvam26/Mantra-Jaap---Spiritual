const CACHE_NAME = 'mantra-jaap';
const urlsToCache = [
  '/',
  '/static/logo.png',
  '/static/audio/bansuri_bg.mp3'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});