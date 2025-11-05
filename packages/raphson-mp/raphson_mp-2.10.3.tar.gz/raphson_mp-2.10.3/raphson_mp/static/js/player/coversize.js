// Ensures combined height of album cover and lyrics box never exceed 100vh
// I am convinced this should be possible with just CSS, but I can't figure it out yet.

class CoverSize {
    #layout = /** @type {HTMLSelectElement} */ (document.getElementById('debug-layout'));
    #lyricsBox = /** @type {HTMLDivElement} */ (document.getElementById('lyrics-box'));
    #coverBox = /** @type {HTMLDivElement} */ (document.getElementById('album-cover-box'));
    #leftSidebar = /** @type {HTMLDivElement} */ (document.getElementById('left-sidebar'));
    #rightSidebar = /** @type {HTMLDivElement} */ (document.getElementById('right-sidebar'));
    #sidebars = /** @type {HTMLDivElement} */ (document.getElementById('sidebars'));

    constructor() {
        const resizeObserver = new ResizeObserver(() => {
            // delay to avoid infinite resize loop
            requestAnimationFrame(() => this.#resizeCover());
        });
        resizeObserver.observe(this.#lyricsBox);
        resizeObserver.observe(document.body);
        this.#layout.addEventListener('input', () => this.#resizeCover());
    }

    /**
     * @param {string} value
     */
    #setMaxHeight(value) {
        // Experimenting with various layouts. See debug menu (press 'd').
        const layout = this.#layout.value;
        this.#coverBox.style.maxHeight = value;
        if (layout == "narrow_cover") {
            this.#leftSidebar.style.maxWidth = '';
            this.#rightSidebar.style.maxWidth = '';
            this.#sidebars.style.gridTemplateColumns = '';
            this.#coverBox.style.maxWidth = value;
            this.#lyricsBox.style.maxWidth = '';
        } else if (layout == "narrow_cover_lyrics") {
            this.#leftSidebar.style.maxWidth = '';
            this.#rightSidebar.style.maxWidth = '';
            this.#sidebars.style.gridTemplateColumns = '';
            this.#coverBox.style.maxWidth = value;
            this.#lyricsBox.style.maxWidth = value;
        } else if (layout == "off_center") {
            this.#leftSidebar.style.maxWidth = '';
            this.#rightSidebar.style.maxWidth = value;
            this.#sidebars.style.gridTemplateColumns = 'auto ' + value;
            this.#coverBox.style.maxWidth = value;
            this.#lyricsBox.style.maxWidth = '';
        } else if (layout == "equal_width") {
            this.#leftSidebar.style.maxWidth = value;
            this.#rightSidebar.style.maxWidth = value;
            this.#sidebars.style.gridTemplateColumns = '';
            this.#coverBox.style.maxWidth = '';
            this.#lyricsBox.style.maxWidth = '';
        } else if (layout == "equal_width_fixed") {
            const lyricsHeight = window.getComputedStyle(document.body).getPropertyValue('--lyrics-height');
            const coverSize = `calc(100vh - 3*var(--gap) - ${lyricsHeight})`;
            this.#leftSidebar.style.maxWidth = coverSize;
            this.#rightSidebar.style.maxWidth = coverSize;
            this.#sidebars.style.gridTemplateColumns = '';
            this.#coverBox.style.maxHeight = coverSize;
            this.#coverBox.style.maxWidth = coverSize;
            this.#lyricsBox.style.maxWidth = coverSize;
            this.#lyricsBox.style.height = lyricsHeight;
        }

        console.debug('coversize: max height changed:', value);
    }

    #resizeCover() {
        // Do not set max height in single column interface
        if (document.body.clientWidth <= 950) {
            this.#setMaxHeight('none');
            return;
        }

        if (this.#lyricsBox.hidden) {
            // No lyrics
            this.#setMaxHeight(`calc(100vh - 2*var(--gap))`);
            return;
        }

        this.#setMaxHeight(`calc(100vh - 3*var(--gap) - ${this.#lyricsBox.clientHeight}px)`);
    }
}

export const coverSize = new CoverSize();
