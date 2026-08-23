'use strict';

/* Kopfzeile bleibt beim Scrollen stehen und bekommt dann einen Hintergrund.
   Der Zustand haengt am body, weil auch die Schaltflaechen im Hero darauf
   reagieren. Wird von allen Seiten geladen, auch von denen ohne weiteres
   Skript. */
const SCROLL_THRESHOLD = 24;

let headerFrame = null;

const updateHeaderState = () => {
    document.body.classList.toggle('is-scrolled', window.scrollY > SCROLL_THRESHOLD);
    headerFrame = null;
};

const requestHeaderUpdate = () => {
    if (headerFrame) return;
    headerFrame = requestAnimationFrame(updateHeaderState);
};

updateHeaderState();
window.addEventListener('scroll', requestHeaderUpdate, { passive: true });
