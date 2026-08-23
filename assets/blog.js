'use strict';

/* Reading progress and table of contents */
const progressBar = document.querySelector('.reading-progress span');
const tocLinks = [...document.querySelectorAll('.article-toc a')];
const observedSections = tocLinks
    .map((link) => document.querySelector(link.getAttribute('href')))
    .filter(Boolean);

let progressFrame;

const updateReadingProgress = () => {
    const scrollableHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = scrollableHeight > 0 ? window.scrollY / scrollableHeight : 0;

    progressBar.style.transform = `scaleX(${Math.min(1, Math.max(0, progress))})`;
    progressFrame = null;
};

const requestProgressUpdate = () => {
    if (!progressFrame) {
        progressFrame = requestAnimationFrame(updateReadingProgress);
    }
};

if (observedSections.length) {
    const sectionObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) return;

            tocLinks.forEach((link) => {
                const isCurrent = link.getAttribute('href') === `#${entry.target.id}`;

                if (isCurrent) {
                    link.setAttribute('aria-current', 'true');
                } else {
                    link.removeAttribute('aria-current');
                }
            });
        });
    }, { rootMargin: '-20% 0px -65% 0px' });

    observedSections.forEach((section) => sectionObserver.observe(section));
}

updateReadingProgress();
window.addEventListener('scroll', requestProgressUpdate, { passive: true });
window.addEventListener('resize', requestProgressUpdate);

/* Share dialog */
const shareButton = document.querySelector('[data-share-button]');

if (shareButton) {
    const shareDialog = document.createElement('dialog');
    const articleTitle = document.querySelector('h1')?.textContent.trim() || document.title;

    shareDialog.className = 'share-dialog';
    shareDialog.setAttribute('aria-labelledby', 'share-dialog-title');
    shareDialog.innerHTML = `
        <div class="share-dialog__inner">
            <div class="share-dialog__header">
                <div>
                    <p class="share-dialog__kicker">Beitrag teilen</p>
                    <h2 id="share-dialog-title">Auf welcher Plattform?</h2>
                </div>
                <button class="share-dialog__close" type="button" data-share-close aria-label="Teilen-Dialog schließen">×</button>
            </div>
            <div class="share-options">
                <a class="share-option" data-share-platform="whatsapp" target="_blank" rel="noopener noreferrer"><span class="share-option__icon">WA</span>WhatsApp</a>
                <a class="share-option" data-share-platform="facebook" target="_blank" rel="noopener noreferrer"><span class="share-option__icon">f</span>Facebook</a>
                <a class="share-option" data-share-platform="linkedin" target="_blank" rel="noopener noreferrer"><span class="share-option__icon">in</span>LinkedIn</a>
                <a class="share-option" data-share-platform="x" target="_blank" rel="noopener noreferrer"><span class="share-option__icon">X</span>X / Twitter</a>
                <a class="share-option" data-share-platform="email"><span class="share-option__icon">@</span>E-Mail</a>
                <button class="share-option" type="button" data-copy-link><span class="share-option__icon">⧉</span>Link kopieren</button>
                <button class="share-option" type="button" data-native-share hidden><span class="share-option__icon">•••</span>Weitere Apps</button>
            </div>
            <p class="share-dialog__privacy">Erst nach deiner Auswahl öffnet sich der gewählte Dienst. Dieser Blog lädt keine Inhalte oder Tracker der Plattformen.</p>
            <p class="share-dialog__status" data-share-status aria-live="polite"></p>
        </div>`;

    document.body.appendChild(shareDialog);

    const shareStatus = shareDialog.querySelector('[data-share-status]');
    const nativeShareButton = shareDialog.querySelector('[data-native-share]');

    const updateShareLinks = () => {
        const pageUrl = window.location.href;
        const encodedUrl = encodeURIComponent(pageUrl);
        const encodedTitle = encodeURIComponent(articleTitle);
        const encodedMessage = encodeURIComponent(`${articleTitle}: ${pageUrl}`);

        shareDialog.querySelector('[data-share-platform="whatsapp"]').href = `https://wa.me/?text=${encodedMessage}`;
        shareDialog.querySelector('[data-share-platform="facebook"]').href = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
        shareDialog.querySelector('[data-share-platform="linkedin"]').href = `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`;
        shareDialog.querySelector('[data-share-platform="x"]').href = `https://twitter.com/intent/tweet?text=${encodedTitle}&url=${encodedUrl}`;
        shareDialog.querySelector('[data-share-platform="email"]').href = `mailto:?subject=${encodedTitle}&body=${encodedMessage}`;
        shareStatus.textContent = '';
    };

    const copyCurrentLink = async () => {
        try {
            await navigator.clipboard.writeText(window.location.href);
        } catch (error) {
            const temporaryInput = document.createElement('textarea');
            temporaryInput.value = window.location.href;
            temporaryInput.className = 'clipboard-helper';
            document.body.appendChild(temporaryInput);
            temporaryInput.select();
            document.execCommand('copy');
            temporaryInput.remove();
        }

        shareStatus.textContent = 'Link wurde kopiert.';
    };

    shareButton.addEventListener('click', async () => {
        updateShareLinks();

        if (typeof shareDialog.showModal === 'function') {
            shareDialog.showModal();
        } else if (navigator.share) {
            await navigator.share({ title: articleTitle, url: window.location.href });
        } else {
            await copyCurrentLink();
        }
    });

    shareDialog.querySelector('[data-share-close]').addEventListener('click', () => shareDialog.close());
    shareDialog.querySelector('[data-copy-link]').addEventListener('click', copyCurrentLink);

    shareDialog.addEventListener('click', (event) => {
        if (event.target === shareDialog) shareDialog.close();
    });

    if (navigator.share) {
        nativeShareButton.hidden = false;
        nativeShareButton.addEventListener('click', async () => {
            try {
                await navigator.share({ title: articleTitle, url: window.location.href });
                shareDialog.close();
            } catch (error) {
                if (error.name !== 'AbortError') shareStatus.textContent = 'Teilen war nicht möglich.';
            }
        });
    }
}
