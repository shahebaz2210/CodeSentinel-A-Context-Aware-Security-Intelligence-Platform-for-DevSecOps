# Design Doc — CodeSentinel
### A Context-Aware Security Intelligence Platform for DevSecOps

**Direction reference:** the current wave of dark-mode "AI agent" SaaS headers on Dribbble (glowing gradient orbs, glass panels, bold geometric display type on near-black) — reinterpreted through the *specific vernacular of security tooling*: diffs, scan traces, gates, severity signal colors, terminal rhythm. Studied for craft direction (not copied): **Linear** (restraint, precision, single-accent discipline), **Vercel** (dark-canvas confidence, monospace data treatment), **GitHub Dark** (the developer's home turf — diff colors, code blocks, PR check semantics that our audience already reads fluently).

> **A note on scope**: this doc defines the visual system and screen-level UX for CodeSentinel's dashboard, finding detail, and AI assistant surfaces — the parts of the product a human actually looks at. Backend/API/data-model decisions are out of scope here (see `Architecture.md`, `API.md`, `Database.md`).

---

## 0. Design Thesis

CodeSentinel's core tension, stated plainly in the product itself, is: **deterministic evidence vs. AI reasoning, always visibly separated, with the human always in control.** The design has to *look* like that's true — not just say it. So the signature move of this system:

> **The Scan Trace** — a single glowing line that visually threads through every stage of the 5-agent pipeline (Repo Analysis → Detection → Intelligence → Risk → Remediation), lighting up each stage as it completes, and terminating at a hard-edged, non-glowing **Gate** component (PASS/WARNING/BLOCK) that is deliberately un-animated, un-gradiented, and rendered in flat color — because the gate is deterministic, not generative, and it should *feel* that way next to everything glowing around it.

Everything AI-generated (explanations, suggested fixes, assistant answers) gets the glow treatment (soft gradient edge, animated entrance). Everything deterministic (scores, gate results, scanner findings) is flat, high-contrast, static. This isn't decoration — it's the product's core trust model made visible.

---

## 1. Token System

### 1.1 Color

| Token | Hex | Usage |
|---|---|---|
| `--bg-canvas` | `#0B0E14` | App background — near-black, slight blue undertone (not pure black, avoids OLED-smear/harshness) |
| `--bg-surface` | `#12161F` | Card/panel background |
| `--bg-surface-raised` | `#1A1F2B` | Modals, popovers, dropdowns |
| `--border-hairline` | `#242B38` | Default borders, dividers |
| `--border-focus` | `#7C6CFF` | Focus rings, active states |
| `--text-primary` | `#F3F5F9` | Headings, primary content |
| `--text-secondary` | `#9AA4B8` | Supporting text, metadata |
| `--text-tertiary` | `#5C6478` | Disabled, placeholder, timestamps |
| `--accent-ai` | `#7C6CFF` | The single AI/brand accent — used for anything AI-generated: explanations, suggested fixes, assistant, glow effects |
| `--accent-ai-glow` | `#7C6CFF` at 24% opacity, 40px blur | Ambient glow behind AI-touched components only |
| `--signal-critical` | `#F0465C` | Critical severity, BLOCK gate |
| `--signal-high` | `#FF8A4C` | High severity |
| `--signal-medium` | `#F5C542` | Medium severity, WARNING gate |
| `--signal-low` | `#5B9DF5` | Low severity |
| `--signal-pass` | `#3DD68C` | PASS gate, resolved findings, validated patches |

**Why this palette, not the generic AI-purple-gradient-on-black default:** the accent (`--accent-ai`) is used *exclusively* for AI-originated content — it never touches a scanner finding, a risk score, or a gate result. Severity colors are borrowed from the vocabulary developers already trust (git diff red/green, CI red/yellow/green) rather than invented — so a developer's existing muscle memory transfers instantly. The gate colors are flat/opaque; the AI accent is the only thing allowed to glow. That asymmetry *is* the brand.

### 1.2 Typography

| Role | Typeface | Notes |
|---|---|---|
| Display (H1/Hero) | **Space Grotesk**, 600–700 | Geometric, slightly technical, confident at large sizes without feeling corporate |
| UI / Body | **Inter**, 400–500 | Neutral, highly legible at small sizes, the workhorse |
| Data / Code / Monospace | **IBM Plex Mono**, 400–500 | File paths, line numbers, finding IDs, risk scores, code snippets, CWE/OWASP tags — anything that is *data*, not prose, is set in mono to visually separate "fact" from "explanation" |

**Type scale (desktop):**
| Token | Size / Line-height | Weight | Usage |
|---|---|---|---|
| `display-xl` | 56px / 1.05 | 700 | Landing hero headline only |
| `display-lg` | 36px / 1.15 | 600 | Page titles (Dashboard, Finding Detail) |
| `heading-md` | 22px / 1.3 | 600 | Section headers, card titles |
| `heading-sm` | 16px / 1.4 | 600 | Component labels, table headers |
| `body-md` | 15px / 1.55 | 400 | Default body text |
| `body-sm` | 13px / 1.5 | 400 | Secondary/meta text |
| `mono-md` | 14px / 1.5 | 500 | Code, file paths, risk scores |
| `mono-sm` | 12px / 1.4 | 400 | Line numbers, timestamps, IDs |

### 1.3 Spacing & Radius
- Base unit: **4px**. Scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64.
- Card padding: 24px. Section gaps: 32–48px.
- Radius: `--radius-sm: 6px` (buttons, inputs, tags), `--radius-md: 10px` (cards), `--radius-lg: 16px` (modals, hero panels). The Gate component uses `--radius-sm` only — sharper, harder-edged than surrounding cards, reinforcing "this is not soft/generative."

### 1.4 Breakpoints
| Name | Width | Behavior |
|---|---|---|
| `mobile` | < 640px | Single column, dashboard cards stack, Finding Detail becomes full-screen drawer, assistant becomes bottom sheet |
| `tablet` | 640–1023px | 2-column dashboard grid, sidebar collapses to icon rail |
| `desktop` | 1024–1439px | Full 3-column dashboard, persistent sidebar |
| `wide` | ≥ 1440px | Max content width 1280px, centered, extra breathing room — never stretches to full width (avoids the "everything is huge" feel on ultrawide monitors) |

---

## 2. User Journey — Step by Step

This traces the primary path: a developer connects a repo, runs a scan, reviews a finding, and (in the PR context) makes a merge decision.

**Step 1 — Connect (first-time only).**
Developer lands on an empty-state screen: "Connect a repository to start your first scan." Single primary action: **Connect with GitHub** (OAuth). No dashboard chrome shown yet — this is a focused, single-purpose screen.

**Step 2 — Select & Scan.**
After OAuth, developer sees their repo list (from GitHub API). Selects one. Clicks **Run Repository Scan**. Button enters a loading state; a toast confirms "Scan started" and the developer is taken to the Dashboard, which now shows a live **Scan Trace** — the 5-agent pipeline visualized as a glowing line moving left to right through five labeled nodes (Repo Analysis, Detection, Intelligence, Risk, Remediation), each node flipping from dim → lit as its agent completes.

**Step 3 — Review Results (Dashboard).**
Scan completes. Dashboard now shows: overall security score (large, flat number — not glowing, it's deterministic), severity breakdown (4 signal-colored counts), the Gate result badge (PASS/WARNING/BLOCK, flat/sharp-edged), and a findings list ordered by severity.

**Step 4 — Drill into a Finding.**
Developer clicks a finding row → **Finding Detail** view opens (side panel on desktop, full-screen on mobile). Top half is flat/factual (severity, risk score, file/line, code snippet — all mono type, all static). Bottom half is AI-touched and glow-treated (root cause, impact, attack scenario, suggested fix) — visually and physically separated by a hairline divider labeled "AI Analysis," so the developer always knows which half is evidence and which half is interpretation.

**Step 5 — Evaluate the Suggested Fix.**
Developer clicks **Validate Fix**. A compact status stepper appears inline (Applying patch → Running tests → Re-scanning → Result), each step ticking off in real time. On PASS, the fix becomes available to copy/apply, marked with a small "Validated" badge (flat green, not AI-purple — once validated, it's earned deterministic status). On FAIL, the fix is visually withdrawn (grayed, struck through) with a one-line reason.

**Step 6 — PR Context (if this was a PR scan).**
On GitHub itself, the developer sees a native GitHub Check + PR comment (CodeSentinel does not design GitHub's own UI, but the comment content follows the same voice rules — see §8 Accessibility & Content). The comment states the check result plainly and links back to the CodeSentinel Finding Detail view for anything beyond a one-line summary. The comment never says "approved" — only "checks passed" or "N issues found," and always ends with a link, not an embedded judgment.

**Step 7 — Ask the Assistant (optional, any point).**
A persistent, collapsed assistant affordance sits bottom-right (glow-accented icon, consistent with "this is AI"). Developer clicks it, types a question ("what should I fix first?"), sees a streaming response grounded in the current scan — rendered in the same AI-glow visual language as the Finding Detail's AI Analysis section, so the *visual grammar* of "this is AI reasoning" is consistent everywhere it appears in the product.

**Step 8 — Human Decision.**
Developer approves or requests changes **on GitHub**, not in CodeSentinel. CodeSentinel's dashboard reflects the outcome (rescan trend line ticks up/down) but never presents a "CodeSentinel approved this" state anywhere, on any screen.

---

## 3. Layout Per Screen

### 3.1 Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ [Logo]      Repo: acme/webapp ▾        [Assistant●] [Avatar] │  ← 64px header, sticky
├───────────┬─────────────────────────────────────────────┤
│           │  Security Score          Gate: ▣ PASS         │
│  Sidebar  │  ┌───────────┐  Critical 2  High 5  Med 11  Low 20
│  (icons + │  │    82     │                                 │
│  labels)  │  │  / 100    │  ── Scan Trace ──○──○──○──○──○  │
│           │  └───────────┘  (5 agent nodes, glow-lit)      │
│  - Scans  ├─────────────────────────────────────────────┤
│  - Repos  │  Findings                          [Filter ▾] │
│  - Trends │  ┌─────────────────────────────────────────┐ │
│  - Policy │  │ ● CRITICAL  SQL Injection   login.js:42  │ │
│           │  ├─────────────────────────────────────────┤ │
│           │  │ ● HIGH      Hardcoded Secret  .env:3     │ │
│           │  └─────────────────────────────────────────┘ │
│           │  Scan History & Trend ────────────────────── │
│           │  [sparkline chart, 90 days]                   │
└───────────┴─────────────────────────────────────────────┘
```
**Hierarchy:** Score and Gate are the two largest, most flat/static elements — top-left, first-read position (Western F-pattern). Scan Trace sits immediately beside them as the "is this live/finished" signal. Findings list is the workhorse below the fold trigger, sorted severity-first by default. Trend chart is deliberately last — it's context, not the headline.

**Spacing:** 32px gutter between sidebar and content; 24px between dashboard cards; 16px internal card padding minimum, 24px for the score/gate hero row.

**Breakpoints:** Desktop = 3-column card grid for score/gate/trace row. Tablet = stacks to 2 columns (score+gate paired, trace full-width below). Mobile = fully stacked, sidebar collapses to a bottom tab bar (Scans / Repos / Trends / Assistant).

### 3.2 Finding Detail (side panel, desktop / full-screen, mobile)
```
┌───────────────────────────────────┐
│ ✕  SQL Injection · login.js:42     │
├───────────────────────────────────┤
│ Severity  CRITICAL      Risk 91/100│  ← flat, mono, static
│ Confidence  High     CWE-89 · OWASP A03
│ ┌─────────────────────────────┐   │
│ │ 40  const query = `SELECT... │   │  ← code snippet, mono, line-numbered
│ │ 42▶ ...${userInput}`;        │   │
│ └─────────────────────────────┘   │
├─── AI Analysis ─── (glow divider) ─┤
│ ✦ Root Cause                       │  ← soft purple glow edge on section
│ ✦ Impact                           │
│ ✦ Attack Scenario                  │
│ ✦ Suggested Fix        [Validate]  │
└───────────────────────────────────┘
```
**Hierarchy:** Factual/deterministic data always above the fold, AI analysis always below a clearly labeled divider — never interleaved. This ordering is a hard rule, not a preference: it's the trust model.

**Spacing:** 24px padding throughout; 16px between factual data rows; 32px gap before the AI Analysis divider (visually "breathes" more, signaling a mode change).

**Breakpoints:** Desktop = 420px fixed-width side panel, pushes content left (doesn't overlay). Mobile = full-screen takeover, standard back-navigation.

### 3.3 AI Security Assistant
Desktop: collapsed as a 48px circular glow-accented button, bottom-right, persistent across the dashboard and finding views. Expands to a 380px-wide panel, docked bottom-right, not a full modal — deliberately keeps the dashboard visible/referenceable behind it. Mobile: expands to a bottom sheet at 80% viewport height.

---

## 4. Component Inventory (with states)

### 4.1 Severity Tag
- **Default:** filled pill, signal color at 16% bg opacity, full-opacity text and dot.
- **Hover** (in a list row): row background lifts to `--bg-surface-raised`, tag unchanged (tags are data, not interactive).
- No loading/error/empty state (static label).

### 4.2 Gate Badge (PASS / WARNING / BLOCK)
- **PASS:** flat `--signal-pass` fill, white text, checkmark icon, `--radius-sm`.
- **WARNING:** flat `--signal-medium` fill, dark text (contrast), triangle icon.
- **BLOCK:** flat `--signal-critical` fill, white text, octagon/stop icon.
- **Loading (scan in progress):** neutral gray outline, pulsing border opacity (not the AI glow — this is a deterministic-pending state, so it pulses rather than glows), label "Evaluating…".
- No hover state — this is a status readout, not a control.

### 4.3 Scan Trace (5-node pipeline)
- **Pending node:** dim outline circle, `--text-tertiary`.
- **Active node:** `--accent-ai` fill + glow, subtle scale pulse (1.0 → 1.06 → 1.0).
- **Complete node:** solid `--accent-ai` fill, glow fades to a thin static ring (settles — doesn't stay animated once done).
- **Error node** (agent failed): `--signal-critical` outline, no glow (errors are factual, not generative), small exclamation.
- **Connecting line:** gradient trail from last-complete to active node; unlit segments are a flat 1px hairline.

### 4.4 Finding Row (list item)
- **Default:** severity dot + type + file:line, `--bg-surface`, hairline bottom border.
- **Hover:** background → `--bg-surface-raised`, 120ms ease-out, cursor pointer, chevron fades in on the right.
- **Selected/Active** (detail panel open for this row): left border 2px `--accent-ai` — the only place a list item gets the AI accent, since selecting it is about to surface AI analysis.
- **Empty state** (zero findings): centered, single line "No findings in this scan" + a flat `--signal-pass` checkmark, no illustration (avoid over-designing a good-news state — keep it quiet, not celebratory-loud).
- **Loading (scan running):** skeleton rows, shimmer at 1.5s loop, `--bg-surface-raised` base.

### 4.5 AI Analysis Card (root cause / impact / attack scenario / suggested fix)
- **Default:** `--bg-surface`, 1px border in `--accent-ai` at 24% opacity, soft outer glow (24px blur, 12% opacity).
- **Loading (generating):** border opacity animates 24%→48%→24% (breathing), placeholder text "Generating explanation…" in `--text-tertiary`.
- **Error** (LLM/RAG call failed): border switches to flat `--signal-medium`, glow removed, message: "Couldn't generate an explanation. [Retry]" — errors always drop the glow, because a failure is a fact, not a generation.
- **Streaming text:** characters append with no per-character animation (avoid gimmicky typewriter effect); a slim pulsing cursor block at the end signals "still generating."

### 4.6 Validate Fix — Status Stepper
- **Steps:** Applying patch → Running tests → Re-scanning → Result.
- **Pending step:** gray dot, `--text-tertiary` label.
- **Active step:** `--accent-ai` dot with glow + spinner ring.
- **Complete step:** flat `--signal-pass` checkmark (deterministic outcome per step — no glow once decided).
- **Fail terminal state:** `--signal-critical` dot on the failed step, stepper halts, one-line reason shown below, "Reject Fix" wording used explicitly (matches product's own language — never soften this to "unavailable").
- **Empty/idle:** stepper not rendered until "Validate Fix" is clicked; button shows default state pre-click.

### 4.7 Repository Score Ring
- **Default:** circular progress ring, flat single color mapped to score band (≥80 pass-green, 50–79 medium-amber, <50 critical-red), center shows mono numeral, static — no glow, no animation once loaded (it's a fact, not a generation).
- **Loading:** ring shows an indeterminate rotating arc, `--text-tertiary`, until first score is computed.
- **First-scan empty state:** ring shown as a dashed outline with "—" center value, label "Awaiting first scan."

### 4.8 Assistant Panel
- **Collapsed (idle):** 48px circle, `--accent-ai` fill, ambient glow pulse (slow, 3s loop, barely perceptible — signals "available" without nagging).
- **Expanded / empty:** panel open, no messages yet, placeholder prompts shown as tappable chips ("What should I fix first?", "Why did my score change?").
- **User message:** right-aligned, `--bg-surface-raised`, no glow (user input is not AI-generated).
- **Assistant message (streaming):** left-aligned, glow-edged card matching §4.5 treatment, streaming cursor.
- **Assistant message (grounded citation present):** small inline reference chip ("Finding F-1024," "OWASP A03") — mono type, clickable, jumps to that Finding Detail.
- **Error:** flat red-bordered message, "Something went wrong — try again," retry button, glow removed.

### 4.9 Buttons
- **Primary (`Connect with GitHub`, `Run Scan`):** solid `--accent-ai` fill, white text, `--radius-sm`. Hover: 8% lighten + 1px lift (2px shadow). Active/pressed: 4% darken, no lift. Disabled: 40% opacity, no hover response. Loading: label replaced with spinner, width locked (no layout shift).
- **Secondary (`Retry`, `Cancel`):** transparent fill, `--border-hairline` border, `--text-primary` text. Hover: border → `--text-secondary`.
- **Destructive (`Reject Fix` confirmation, if surfaced as an action):** `--signal-critical` border, transparent fill, text in signal-critical — reserved, used sparingly.

---

## 5. Motion

| Element | Animation | Duration | Easing | Rationale |
|---|---|---|---|---|
| Scan Trace node activation | scale pulse 1.0→1.06→1.0 + glow fade-in | 600ms | `cubic-bezier(0.22, 1, 0.36, 1)` (ease-out-back, subtle) | Reads as "processing," settles cleanly — not bouncy/playful, this is infrastructure work |
| Scan Trace line fill | width/opacity grow, node-to-node | 400ms per segment | ease-out | Sequential, not simultaneous — reinforces "pipeline," not "loading bar" |
| AI Analysis card entrance | opacity 0→1 + 8px translate-Y | 240ms | ease-out | Quick, single easing — no bounce (AI content should feel considered, not flashy) |
| AI Analysis loading breathe | border-opacity 24%→48%→24% | 1800ms loop | ease-in-out | Ambient, low-attention — this is a background "still thinking" signal, not a focal animation |
| Finding row hover | background-color | 120ms | ease-out | Fast enough to feel responsive, not sluggish |
| Gate badge (pending→result) | cross-fade, no motion on the shape itself | 200ms | linear | Deterministic state changes should feel instant and flat — motion here would undercut the "this is a fact" read |
| Assistant collapsed pulse | opacity 100%→70%→100% ambient glow | 3000ms loop | ease-in-out | Barely perceptible — an invitation, not a distraction |
| Streaming text cursor | opacity blink | 800ms loop | step (no ease) | Standard terminal-cursor convention, matches developer vernacular |
| Modal/panel open (Finding Detail) | translate-X from right edge (desktop) / translate-Y from bottom (mobile) | 280ms | `cubic-bezier(0.16, 1, 0.3, 1)` | Directional motion ties the panel to its trigger — "this came from that row" |
| Toast (e.g., "Scan started") | slide-up + fade | 200ms in / 160ms out | ease-out | Quick and out of the way |

**Global rule:** nothing glows or breathes unless it originated from the LLM. Deterministic UI (scores, gates, severity, validated results) transitions with instant cross-fades or flat easing only — no pulse, no glow, ever. This is the single motion rule that encodes the product's trust model, and it should never be broken for visual consistency's sake.

**Reduced motion:** with `prefers-reduced-motion: reduce`, all pulse/breathe/scale animations are replaced with instant state changes (opacity-only cross-fades ≤100ms); the Scan Trace still communicates progress via node fill state, not motion.

---

## 6. Accessibility Notes

- **Color is never the only signal.** Every severity tag carries a text label ("CRITICAL," "HIGH") alongside its color dot — never color alone. Gate badges carry both icon and text (✓ PASS, ▲ WARNING, ⛔ BLOCK).
- **Contrast:** `--text-primary` (#F3F5F9) on `--bg-canvas` (#0B0E14) = ~16.8:1 (exceeds AAA for normal text). `--text-secondary` (#9AA4B8) on canvas = ~7.1:1 (passes AAA for normal text, comfortably clears AA for small text). Signal colors were chosen/checked to hit at least AA (4.5:1) as text-on-dark; where a signal color is used as a *fill* with white/dark text on top (badges), text color flips (dark text on `--signal-medium` amber, white text on the others) to maintain contrast — this is why the Gate Badge spec above calls out "dark text" specifically for WARNING.
- **Focus states:** every interactive element gets a visible 2px `--border-focus` outline with 2px offset — never suppressed, including inside the Assistant panel and Finding Detail (a common miss in panel/drawer UIs).
- **Keyboard navigation:** Finding list is fully arrow-key navigable; Enter opens the detail panel; Escape closes it and returns focus to the triggering row (not to page top — preserves place).
- **Screen reader labeling:** the Scan Trace's node states must be exposed via `aria-live="polite"` region announcing stage transitions ("Repository Analysis complete, Security Detection in progress") — the visual pipeline metaphor has no meaning to a non-visual user without this.
- **AI-generated content must be identified programmatically**, not just visually — the "AI Analysis" divider is a real heading (`<h3>AI Analysis</h3>`) with an `aria-label` clarifying it's AI-generated content, not decorative text, so assistive tech users get the same evidence/interpretation distinction sighted users get from the glow treatment.
- **Motion sensitivity:** all ambient/looping animations (Assistant pulse, AI card breathe, streaming cursor) respect `prefers-reduced-motion` per §5. Scan Trace pulse also downgrades to a static fill-state change.
- **Streaming text:** live-updating assistant responses use `aria-live="polite"` (not `assertive`, to avoid interrupting a screen reader mid-sentence) and should not steal focus while streaming.
- **Touch targets:** minimum 44×44px for all tappable elements on mobile (severity filter chips, assistant collapse/expand button, finding row full-width tap area).

---

## 7. Signature Element Recap

If this design system is remembered for one thing, it should be the **Scan Trace → Gate handoff**: a glowing, alive, AI-flavored pipeline visualization that terminates in a flat, static, unglowing badge — the moment where generative process becomes deterministic fact. That single visual transition, repeated consistently across the Dashboard, Finding Detail, and even the PR comment's tone, *is* CodeSentinel's core design principle (deterministic evidence, AI reasoning, human authority) made legible without a single word of explanation.
