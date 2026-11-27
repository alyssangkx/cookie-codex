# Web Interface Guidelines audit, 27 Nov 2026

First run of the `web-design-guidelines` skill (`.claude/skills/web-design-guidelines/`, rules pinned at
vercel-labs/web-interface-guidelines 434b7f9). Three Sonnet reviewers, one per page group; no files were edited. **No
high-severity finding** (nothing breaks use outright). Findings are the reviewers' claims, unverified until fixed and
checked in the browser; line numbers are as of commit 80adecc.

## Medium (worth fixing)

| # | Where | Rule | Problem | Fix |
|---|---|---|---|---|
| M1 | quiz 1661, 1689, 1854; Base 206-218 | Focus not hidden by sticky/fixed bars | The pinned word box, phrase bank and paper status bar (top) and the sync banner (bottom) can cover the focused blank or input | `scroll-margin-top` on blanks/chips/options; `html { scroll-padding-bottom }` for the banner |
| M2 | quiz 834, 1091, 1098, 1108 | Autofocus sparingly on mobile | Focusing the typed box opens the phone keyboard before the stem is read | Auto-focus only when `(pointer: fine)` |
| M3 | quiz 56 | Live regions | `#feedback` is `hidden` until filled, so screen readers may skip it | Keep the live region rendered, change only its content |
| M4 | quiz, parent, school, train, global | Hover/active states | Many buttons (`.primary`, `.chip`, `.phrase`, `.go`, `.t-act`, `.btn`, nav links) have no hover or active state | One shared `@media (hover:hover)` hover + `:active` rule |
| M5 | quiz, parent, global | `touch-action: manipulation` | Only `.phrase` sets it; other buttons keep the double-tap delay | `a, button, summary, label { touch-action: manipulation }` in global.css |
| M6 | quiz 505; parent 401, 404 | Image dimensions | Science and exam-page images have no width/height: layout shifts on load | Width/height from the figure data, or `aspect-ratio` |
| M7 | parent 659-661 | Semantic HTML | The new subject "Retest N" button sits inside `<summary>` (invalid; read as part of the fold's name) | Put it beside the fold, with `aria-label` naming the subject |
| M8 | parent 887, 913 | Focus management | After a save the panels re-render: focus drops to the page and open folds close | Restore focus and open folds after render |
| M9 | parent 24-27, 936-941 | ARIA tabs | `role=tablist/tab` without arrow keys or tabpanels | Add the keyboard pattern, or drop the tab roles |
| M10 | parent 806-875 | Submit state | Add child / Set PIN / Delete can be pressed twice while saving | Disable with "Adding…" until settled |
| M11 | parent 810-830 | Form errors | Errors appear below the form, focus not moved | Focus the bad input, `aria-describedby` |
| M12 | parent 449, 604, 635, 516 | Async updates | "Loading questions…" swaps and `#dash-msg` (made inside innerHTML) are not announced | Persistent live regions, `aria-busy` |
| M13 | parent 622-626 | Large lists | Mistakes/Retest render every question at once | `content-visibility: auto`, cap ~50 per subject with "Show more" |
| M14 | school [sub] 88, 312 | Semantic HTML | A disabled Start is an `<a>` without href: no role, not focusable, reason unreachable | `<button aria-disabled>` + `aria-describedby` |
| M15 | school [sub] 36, 85, 217, 332 | Async updates | `#next-line`, `#c-mtext` rewritten silently; `aria-label` on a bare `<p>` | `aria-live="polite"`; drop the label |
| M16 | train index 96 | Contrast | "Coming soon" school text at opacity .7 is ~3.4:1 | Dashed border instead of opacity |
| M17 | home 99-130 | Headings | No `<h1>` ("Welcome back" is a `<p>`) | Make it the `<h1>` |
| M18 | home 101-102 | Images | Both map images download on every device (one is display:none) | One `<picture>` with a media source, `fetchpriority="high"` |
| M19 | home 118-122 | Semantic HTML | "Coming soon" building is a `span role=link` that goes nowhere | `<button aria-disabled>` |
| M20 | Base 129 | Async updates | The Crumbs balance rewrites the Shop link's name and shifts the header | Separate span with reserved width |

## Low (polish)

Quiz: `…` not `...` (740); `overscroll-behavior: contain` on dialogs (also Base); tap-highlight colour; `user-select: none`
on phrases; a used word-box word marked only visually (needs `aria-disabled`); right vs corrected blank differ only by
colour; report note input lacks `name`; heading levels (h1 then h4); `text-wrap: balance` on headings; long unbroken
option text can overflow; no `theme-color`. Parent: inputs lack `name`/`spellcheck=false`/`autocapitalize=off`;
placeholders without `…`/examples; tab/child not in the URL; numeric columns not tabular; long typed answers can overflow;
`.btn.small`/`.dwrong` 36 px (44 px elsewhere); nested h3 under h3; prompt()+confirm() for delete; hard-coded `en-SG`;
number and unit can wrap apart; range input lacks `aria-valuetext`. School/train/home: initial "0 of N" / "0 of 2" flash
before the script paints; breadcrumb not a `<nav>`; trail labels can collide at 430 px; straight apostrophes;
`<img src="">` placeholders; sprites lazy above the fold; pills `nowrap` at 430 px; endless glow/bob animations
(reduced-motion is honoured).

## Already fine (reviewers' notes)

Skip link and `<main>`; global `:focus-visible` ring; `type="button"` and `aria-pressed` on the quiz controls; labels on
static form controls; `prefers-reduced-motion`; no zoom lock; `esc()` on interpolated text; dialog Esc/Back handling.
