'use strict';

/* Elements and post data */
const searchDialog = document.querySelector('#site-search');
const searchInput = searchDialog?.querySelector('[data-search-input]');
const searchResults = searchDialog?.querySelector('[data-search-results]');
const searchSummary = searchDialog?.querySelector('[data-search-summary]');
const blogPosts = Array.isArray(window.BLOG_POSTS) ? window.BLOG_POSTS : [];

/* Search helpers */
const normalizeSearchText = (value) => value
    .toLocaleLowerCase('de')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

/* Results */
const createSearchResult = (post, index) => {
    const link = document.createElement('a');
    const number = document.createElement('span');
    const copy = document.createElement('span');
    const category = document.createElement('span');
    const title = document.createElement('strong');
    const arrow = document.createElement('span');

    link.className = 'search-result';
    link.href = post.url;
    number.className = 'search-result__index';
    number.textContent = String(index + 1).padStart(2, '0');
    category.className = 'search-result__category';
    category.textContent = `${post.category} · ${post.meta}`;
    title.textContent = post.title;
    arrow.className = 'search-result__arrow';
    arrow.setAttribute('aria-hidden', 'true');
    arrow.textContent = '↗';

    copy.append(category, title);
    link.append(number, copy, arrow);
    return link;
};

const renderSearchResults = (query = '') => {
    const normalizedQuery = normalizeSearchText(query.trim());
    const terms = normalizedQuery.split(/\s+/).filter(Boolean);
    const matches = blogPosts.filter((post) => {
        const haystack = normalizeSearchText([
            post.title,
            post.category,
            post.meta,
            post.excerpt,
            ...post.tags
        ].join(' '));

        return terms.every((term) => haystack.includes(term));
    });

    const orderedMatches = normalizedQuery ? matches : [...matches].reverse();
    searchResults.replaceChildren();

    if (!orderedMatches.length) {
        const empty = document.createElement('p');
        empty.className = 'search-empty';
        empty.textContent = 'Dazu habe ich noch keinen Beitrag gefunden.';
        searchResults.append(empty);
    } else {
        orderedMatches.forEach((post, index) => searchResults.append(createSearchResult(post, index)));
    }

    searchSummary.textContent = normalizedQuery
        ? `${orderedMatches.length} ${orderedMatches.length === 1 ? 'Beitrag' : 'Beiträge'} gefunden`
        : `${orderedMatches.length} Beiträge · Neueste zuerst`;
};

/* Dialog controls */
const openSearch = () => {
    renderSearchResults(searchInput.value);
    searchDialog.showModal();
    requestAnimationFrame(() => searchInput.focus());
};

if (searchDialog) {
    document.querySelectorAll('[data-search-open]').forEach((button) => button.addEventListener('click', openSearch));
    searchDialog.querySelector('[data-search-close]').addEventListener('click', () => searchDialog.close());
    searchInput.addEventListener('input', () => renderSearchResults(searchInput.value));

    searchDialog.addEventListener('click', (event) => {
        if (event.target === searchDialog) searchDialog.close();
    });

    document.addEventListener('keydown', (event) => {
        const isTyping = ['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName);
        if (event.key === '/' && !isTyping && !searchDialog.open) {
            event.preventDefault();
            openSearch();
        }
    });
}
