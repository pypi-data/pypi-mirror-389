import { eventBus, MusicEvent } from "./event.js";
import { queue } from "./queue.js";
import { TimeSyncedLyrics, PlainLyrics, Lyrics } from "../api.js";
import { player } from "./player.js";
import { createIcon, createToast, vars } from "../util.js";
import { setSettingChecked, Setting } from "./settings.js";

class PlayerLyrics {
    #lyricsBox = /** @type {HTMLDivElement} */ (document.getElementById('lyrics-box'));
    #albumCoverBox = /** @type {HTMLDivElement} */ (document.getElementById('album-cover-box'));
    #lyrics = /** @type {Lyrics | null} */ (null);
    #lastLine = /** @type {number | null} */ (null);
    #syncScroll = true;
    #syncScrollEnableTimer = 0;

    constructor() {
        // Quick toggle for lyrics setting
        this.#albumCoverBox.addEventListener('click', () => this.toggleLyrics());

        // Updating synced lyrics is skipped when the page is not visible. Update immediately when it
        // does become visible, without smooth scrolling so the scroll is not noticeable.
        document.addEventListener('visibilitychange', () => this.#updateSyncedLyrics(false));

        // Handle lyrics setting being changed
        Setting.LYRICS.addEventListener('change', () => {
            this.#updateLyrics();
        });

        // Update lyrics when track changes
        eventBus.subscribe(MusicEvent.TRACK_CHANGE, () => {
            const track = queue.currentTrack;
            if (track) {
                this.#lyrics = track.parsedLyrics;
            } else {
                this.#lyrics = null;
            }
            // When lyrics change, current state is no longer accurate
            this.#lastLine = null;
            this.#updateLyrics();
        });

        // Continuously update synced lyrics
        eventBus.subscribe(MusicEvent.PLAYER_POSITION, () => requestAnimationFrame(() => this.#updateSyncedLyrics(true)));

        // Re-enable synced lyrics scrolling on seek
        eventBus.subscribe(MusicEvent.PLAYER_SEEK, () => {
            this.#syncScroll = true;
            requestAnimationFrame(() => this.#updateSyncedLyrics(true));
        });

        // Disable scrolling to current lyrics when the user scrolls manually
        this.#lyricsBox.addEventListener('wheel', () => {
            if (!this.#lyrics || !(this.#lyrics instanceof TimeSyncedLyrics)) {
                return;
            }

            console.debug('lyrics: disable sync scroll');
            this.#syncScroll = false;

            // re-enable sync in 10 seconds, as long as the user does not scroll again
            clearTimeout(this.#syncScrollEnableTimer);
            this.#syncScrollEnableTimer = setTimeout(() => {
                this.#syncScroll = true;
                console.debug('lyrics: re-enable sync scroll');
                this.#updateSyncedLyrics(true);
            }, 10_000);
        });
    }

    toggleLyrics() {
        const checked = !Setting.LYRICS.checked;
        setSettingChecked(Setting.LYRICS, checked);
        if (checked) {
            createToast('text-box', vars.tLyricsEnabled, vars.tLyricsDisabled);
        } else {
            createToast('text-box', vars.tLyricsDisabled, vars.tLyricsEnabled);
        }
    }

    /**
     * @param {boolean} smooth
     */
    #updateSyncedLyrics(smooth) {
        if (!this.#lyrics || !(this.#lyrics instanceof TimeSyncedLyrics)) return;

        if (document.visibilityState != 'visible') return;

        const position = player.getPosition();
        if (position == null) return;

        const currentLine = this.#lyrics.currentLine(position);

        // No need to cause an expensive DOM update if we're still at the same line
        if (currentLine == this.#lastLine) return;

        // Set color and scroll the right element into view
        let i = 0;
        for (const lineElem of this.#lyricsBox.children) {
            if (!(lineElem instanceof HTMLElement)) continue;
            if (i == currentLine) {
                lineElem.classList.remove('secondary-large');

                // Scroll parent so current line is centered
                if (this.#syncScroll) {
                    const totalHeight = this.#lyricsBox.getBoundingClientRect().height;
                    const lineHeight = lineElem.getBoundingClientRect().height;
                    const scrollTarget = Math.max(0, lineElem.offsetTop - totalHeight / 2 + lineHeight / 2);
                    this.#lyricsBox.scrollTo({ "top": scrollTarget, "behavior": smooth ? "smooth" : "instant" });
                }
            } else {
                lineElem.classList.add('secondary-large');
            }

            i++;
        }
    }

    async #searchLyrics() {
        if (!queue.currentTrack) throw new Error();

        if (await queue.currentTrack.searchLyrics()) {
            createToast("sync", vars.tFoundNewLyrics)
        } else {
            createToast("alert-circle", vars.tCouldNotFindNewLyrics);
        }

        this.#lyrics = queue.currentTrack.parsedLyrics;
        this.#updateLyrics();
        this.#updateSyncedLyrics(true);
    }

    #updateLyrics() {
        clearTimeout(this.#syncScrollEnableTimer);

        if (!this.#lyrics || !Setting.LYRICS.checked) {
            this.#lyricsBox.hidden = true;
            return;
        }

        this.#lyricsBox.hidden = false;

        this.#lyricsBox.scrollTo({ "top": 0 });

        const newContent = [];

        if (this.#lyrics instanceof TimeSyncedLyrics) {
            for (const line of this.#lyrics.text) {
                const lineElem = document.createElement('span');
                lineElem.textContent = line.text;
                lineElem.append(document.createElement('br'));
                lineElem.addEventListener('click', () => player.seek(line.startTime));
                lineElem.style.cursor = 'pointer';
                newContent.push(lineElem);
            }

            this.#syncScroll = true;
        } else if (this.#lyrics instanceof PlainLyrics) {
            if (this.#lyrics.text == "[Instrumental]") {
                this.#lyricsBox.hidden = true;
            } else {
                const notTimeSyncedElem = document.createElement('span');
                notTimeSyncedElem.classList.add("secondary");
                notTimeSyncedElem.style.fontStyle = "oblique";
                notTimeSyncedElem.append(vars.tLyricsNotTimeSynced, document.createElement('br'));
                newContent.push(notTimeSyncedElem);

                const lyricsElem = document.createElement('span');
                lyricsElem.textContent = this.#lyrics.text;
                lyricsElem.style.whiteSpace = 'pre-line'; // render newlines
                newContent.push(lyricsElem);
                newContent.push(document.createElement('br'));
            }
        }

        if (!vars.offlineMode) {
            const searchLyricsButton = document.createElement('a');
            searchLyricsButton.classList.add('secondary', 'search-lyrics-button')
            searchLyricsButton.textContent = vars.tSearchNewLyrics;
            searchLyricsButton.addEventListener('click', () => {
                const spinner = createIcon('loading');
                spinner.classList.add('spinning');
                searchLyricsButton.replaceWith(spinner);
                this.#searchLyrics();
            });
            newContent.push(searchLyricsButton);
        }

        this.#lyricsBox.replaceChildren(...newContent);
    }
}

export const lyrics = new PlayerLyrics();
