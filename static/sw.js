const CACHE_NAME = 'mantra-jaap-v2'; // વર્ઝન બદલ્યું છે
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

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      // જો કેશમાં હોય તો ત્યાંથી આપો, નહિતર નેટવર્ક પરથી લો
      return response || fetch(event.request).catch(() => {
          // જો નેટવર્ક પણ ના હોય તો કઈ ના કરો
      });
    })
  );
});

// જૂની કેશ ક્લિયર કરવા માટે
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
    ))
  );
});
