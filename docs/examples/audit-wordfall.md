# ShipPilot audit: WordFall: Word Games

> Real example. Produced in this repository with the `/shippilot:audit` instructions
> ([commands/audit.md](../../commands/audit.md)) from live data fetched by
> [`scripts/fetch_listing.py`](../../scripts/fetch_listing.py). Raw data:
> [audit-wordfall.sources.json](audit-wordfall.sources.json). Wordfall is our own app; it was built and shipped with
> the internal workflows ShipPilot is based on.

## 1. Source

| | App Store | Google Play |
|---|---|---|
| Input URL | https://apps.apple.com/us/app/id6761381016 | https://play.google.com/store/apps/details?id=game.wordfall.app |
| Data source | `https://itunes.apple.com/lookup?id=6761381016&country=us` (public Lookup API) | `https://play.google.com/store/apps/details?id=game.wordfall.app&hl=en&gl=US` (public page, meta tags only) |
| Fetched (UTC) | 2026-10-10T18:48:32+00:00 | 2026-10-10T18:48:32+00:00 |
| Region | us | en/US |
| Missing / unknown | in_app_purchases, keywords, promotional_text, subtitle | average_rating, developer, full_description, screenshots, short_description |

Known from the data: version 1.2.3 (released 2026-10-08), genre Games, price Free,
content rating 12+, 6 iPhone and 6 iPad screenshots,
**0 ratings** in the `us` storefront. The Google Play text below is the page's meta summary,
not the full description.

## 2. What the listing promises

App Store description, first line: *"Follow the letters in WordFall! Join Wiffle, explore different word puzzles and work toward your next personal best."* — it names the game and a mascot but not what you do. The concrete
promises come later: the Vurgun dive, daily word puzzles, live Word Bomb, five word languages.
Google Play meta summary: *"Word game with Word Bomb online, the Vurgun dive and daily word puzzles!"* — this one leads with the concrete modes, which is the
stronger opening.

## 3. Length check

| Store | Field | Length | Limit | Unit | Over? |
|---|---|---|---|---|---|
| App Store | `name` | 20 | 30 | characters | no |
| App Store | `description` | 995 | 4000 | characters | no |
| App Store | `release_notes` | 121 | 4000 | characters | no |
| Google Play | `title` | 20 | 30 | characters | no |

Subtitle, keywords and promotional text are not in Apple's public data, so they could not be checked here; run
`/shippilot:check-metadata` in the app repository for those.

## 4. Quick wins

1. **Lead with the promise.** Start the App Store description with what the Play summary already says (daily
   puzzles, the Vurgun dive, live Word Bomb, five languages) and move "Join Wiffle" to the second sentence.
2. **Rename "Word Tetris" in store text.** The description lists a mode called "Word Tetris"; Tetris is a registered
   trademark of The Tetris Company. A neutral name (for example "Falling Words") avoids a review or takedown risk.
3. **Ask for ratings.** The `us` storefront shows 0 ratings. Prompt for a rating at a happy
   moment (after a solved daily puzzle or a Word Bomb win) with the system review prompt.
4. **Release notes for players first.** The current notes open with *"If you enjoy the game, you can now support
   WordFall with Premium and the packs in the Shop."* Lead with what changed for players, then mention Premium.
5. **Use the unseen fields.** Make sure the subtitle and promotional text are set in App Store Connect; drafts are below.

## 5. Drafts per platform

**iOS** — `name` kept; `subtitle` and `keywords` per locale. The description says the game supports English,
Turkish, German, French and Spanish words, so those are its natural markets.

| Locale | name | subtitle | keywords |
|---|---|---|---|
| en | WordFall: Word Games (20/30 chars) | Daily puzzles & live Word Bomb (30/30 chars) | `daily,puzzle,crossword,anagram,vocabulary,spelling,letters,brain,quiz,multiplayer,dive` (86/100 bytes) |
| tr | WordFall: Word Games (20/30 chars) | Günlük kelime bulmacaları (25/30 chars) | `kelime,bulmaca,günlük,anagram,sözcük,harf,zeka,yarışma,çok oyunculu` (74/100 bytes) |
| de | WordFall: Word Games (20/30 chars) | Worträtsel jeden Tag (20/30 chars) | `wort,rätsel,täglich,buchstaben,anagramm,wortschatz,kreuzworträtsel,quiz` (74/100 bytes) |
| fr | WordFall: Word Games (20/30 chars) | Énigmes de mots chaque jour (27/30 chars) | `mots,énigme,quotidien,lettres,anagramme,vocabulaire,mots croisés,quiz` (71/100 bytes) |
| es | WordFall: Word Games (20/30 chars) | Retos de palabras cada día (26/30 chars) | `palabras,acertijo,diario,letras,anagrama,vocabulario,crucigrama,quiz` (68/100 bytes) |

`promotional_text` (en): Play a new word puzzle every day, dive into Vurgun and beat other players in live Word Bomb matches. Five word languages, one game. (131/170 chars)

**Android** — `title` kept; `short_description` per locale:

| Locale | title | short_description |
|---|---|---|
| en | WordFall: Word Games (20/30 chars) | Daily word puzzles, the Vurgun dive and live Word Bomb in five languages. (73/80 chars) |
| tr | WordFall: Word Games (20/30 chars) | Günlük kelime bulmacaları, Vurgun dalışı ve canlı Word Bomb, beş dilde. (71/80 chars) |
| de | WordFall: Word Games (20/30 chars) | Tägliche Worträtsel, der Vurgun-Tauchgang und Word Bomb online in 5 Sprachen. (77/80 chars) |
| fr | WordFall: Word Games (20/30 chars) | Une énigme de mots par jour, la plongée Vurgun et Word Bomb en ligne, 5 langues. (80/80 chars) |
| es | WordFall: Word Games (20/30 chars) | Retos de palabras diarios, la inmersión Vurgun y Word Bomb online en 5 idiomas. (79/80 chars) |

Lengths were computed against the same limit table as `check-metadata`. Keywords avoid trademarked game names and
words already in the name; they are adapted per market, not translated word for word.

## 6. Screenshot story (proposal — the current images were not analysed)

1. *"A new word puzzle every day"* — the daily puzzle board mid-solve.
2. *"Dive for letters"* — Vurgun with the oxygen bar visible.
3. *"Beat real players"* — a live Word Bomb round with the timer.
4. *"Play in 5 languages"* — the word-language picker.
5. *"A new challenge every day"* — daily challenge progress and the leaderboard.

## 7. Three ad angles

| Angle | Headline | Line | First screen after install |
|---|---|---|---|
| Daily habit | One word puzzle a day | A new word puzzle every day, in five languages. | Today's puzzle, no tutorial first |
| Competition | Beat real players at words | Live Word Bomb: make a word before time runs out. | Word Bomb lobby |
| Language learners | Play in the language you're learning | English, Turkish, German, French or Spanish words. | Word-language picker |

## 8. Next step with ShipPilot

`/shippilot:localize tr de fr es` to write the drafts into `fastlane/metadata` and check limits ·
`/shippilot:ad-creatives google meta` for the three angles · `/shippilot:beta` once the rating prompt ships ·
`/shippilot:grow "does the daily-puzzle ad bring users who finish their first puzzle?"`

