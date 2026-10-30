// Keep shared content anchors when switching between Japanese and English.
// The HTML href remains a working same-page counterpart without JavaScript.
(() => {
    const sharedAnchors = new Set([
        'home', 'research-overview', 'news', 'contact',
        'overview', 'projects', 'achievements', 'publication', 'works'
    ]);
    const links = Array.from(document.querySelectorAll('[data-language-switch]'),
        link => ({ link, href: link.getAttribute('href') }));

    function updateLinks() {
        let anchor = '';
        try {
            anchor = decodeURIComponent(window.location.hash.slice(1));
        } catch {
            // A malformed fragment falls back to the corresponding page.
        }
        const preserveAnchor = sharedAnchors.has(anchor) && document.getElementById(anchor);
        links.forEach(({ link, href }) => {
            link.setAttribute('href', href + (preserveAnchor ? '#' + encodeURIComponent(anchor) : ''));
        });
    }

    updateLinks();
    window.addEventListener('hashchange', updateLinks);
})();
