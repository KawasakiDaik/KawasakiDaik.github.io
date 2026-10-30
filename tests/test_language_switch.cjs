const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../assets/js/language-switch.js'), 'utf8');

function load(href, hash, ids) {
    const links = [0, 1].map(() => ({
        href,
        getAttribute() { return this.href; },
        setAttribute(name, value) { this.href = value; }
    }));
    const listeners = {};
    const window = { location: { hash }, addEventListener(name, fn) { listeners[name] = fn; } };
    const document = {
        querySelectorAll() { return links; },
        getElementById(id) { return ids.includes(id) ? { id } : null; }
    };
    vm.runInNewContext(source, { window, document });
    return { links, window, listeners };
}

test('desktop and mobile preserve shared anchors and the loading query', () => {
    for (const [href, hash] of [
        ['art.html', '#works'],
        ['research_en.html', '#publication'],
        ['index.html?skiploading=true', '#contact']
    ]) {
        const { links } = load(href, hash, [hash.slice(1)]);
        links.forEach(link => assert.equal(link.href, href + hash));
    }
});

test('hash changes update links without accumulating fragments', () => {
    const state = load('research.html', '#publication', ['publication', 'projects']);
    state.window.location.hash = '#projects';
    state.listeners.hashchange();
    state.links.forEach(link => assert.equal(link.href, 'research.html#projects'));
    state.window.location.hash = '';
    state.listeners.hashchange();
    state.links.forEach(link => assert.equal(link.href, 'research.html'));
});

test('unknown, malformed, and absent anchors use the counterpart fallback', () => {
    for (const hash of ['#unknown', '#bad%', '#works']) {
        const { links } = load('art_en.html', hash, []);
        links.forEach(link => assert.equal(link.href, 'art_en.html'));
    }
});

test('encoded valid fragments resolve to the shared anchor', () => {
    const { links } = load('art.html', '#%77orks', ['works']);
    links.forEach(link => assert.equal(link.href, 'art.html#works'));
});
