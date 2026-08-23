'use strict';

/* Mobile navigation */
const navigation = document.querySelector('.nav');
const menuButton = document.querySelector('.menu-button');

const closeNavigation = ({ returnFocus = false } = {}) => {
    navigation.classList.remove('is-open');
    menuButton.setAttribute('aria-expanded', 'false');
    menuButton.setAttribute('aria-label', 'Menü öffnen');
    document.body.classList.remove('menu-open');
    if (returnFocus) menuButton.focus();
};

menuButton.addEventListener('click', () => {
    const isOpen = navigation.classList.toggle('is-open');
    menuButton.setAttribute('aria-expanded', String(isOpen));
    menuButton.setAttribute('aria-label', isOpen ? 'Menü schließen' : 'Menü öffnen');
    document.body.classList.toggle('menu-open', isOpen);
});

/* Jeder Klick im Header schließt das mobile Menü */
navigation.querySelectorAll('a, [data-search-open]').forEach((element) => {
    element.addEventListener('click', () => closeNavigation());
});

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && navigation.classList.contains('is-open')) {
        closeNavigation({ returnFocus: true });
    }
});

window.addEventListener('resize', () => {
    if (window.innerWidth > 1050 && navigation.classList.contains('is-open')) {
        closeNavigation();
    }
});

/* Category tabs */
const categoryTabs = [...document.querySelectorAll('.journal-tab')];
const categoryPanels = [...document.querySelectorAll('.journal-panel')];

const activateCategoryTab = (activeTab) => {
    categoryTabs.forEach((tab) => {
        const isActive = tab === activeTab;
        tab.setAttribute('aria-selected', String(isActive));
        tab.setAttribute('tabindex', isActive ? '0' : '-1');
    });

    categoryPanels.forEach((panel) => {
        panel.hidden = panel.id !== activeTab.getAttribute('aria-controls');
    });

    const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    activeTab.scrollIntoView({ behavior, block: 'nearest', inline: 'center' });
};

categoryTabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activateCategoryTab(tab));
    tab.addEventListener('keydown', (event) => {
        let nextIndex = index;

        if (event.key === 'ArrowRight') nextIndex = (index + 1) % categoryTabs.length;
        if (event.key === 'ArrowLeft') nextIndex = (index - 1 + categoryTabs.length) % categoryTabs.length;
        if (event.key === 'Home') nextIndex = 0;
        if (event.key === 'End') nextIndex = categoryTabs.length - 1;
        if (nextIndex === index) return;

        event.preventDefault();
        categoryTabs[nextIndex].focus();
        activateCategoryTab(categoryTabs[nextIndex]);
    });
});

/* Links that open a category directly */
document.querySelectorAll('[data-open-tab]').forEach((link) => {
    link.addEventListener('click', () => {
        const targetTab = document.getElementById(link.dataset.openTab);
        if (targetTab) activateCategoryTab(targetTab);
    });
});

/* Category from the address, e.g. /#tab-smart-home from an article page */
const openCategoryFromHash = () => {
    const target = document.getElementById(window.location.hash.slice(1));
    if (!target || !target.classList.contains('journal-tab')) return;

    activateCategoryTab(target);
    document.getElementById('projekttagebuch')?.scrollIntoView({
        behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
        block: 'start'
    });
};

openCategoryFromHash();
window.addEventListener('hashchange', openCategoryFromHash);

/* Footer */
document.querySelector('[data-current-year]').textContent = new Date().getFullYear();
