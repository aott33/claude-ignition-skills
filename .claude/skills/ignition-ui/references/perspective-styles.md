# Perspective Styles, Themes, and Style Classes

Applies to: Ignition 8.3.x

Perspective styling is CSS-based. Use the style system hierarchy; never hardcode colors or sizes inline on individual components when a theme variable or style class can serve.

Labels: **[IA docs]** from the IA 8.3 manual; **[live 8.3.9]** verified on a live 8.3.9 Gateway (see the repository's `docs/verification.md`); **[observed in the 8.3.9 module]** / **[observed in the 8.3.9 client]** read from the Perspective module's Java classes or bundled files, or from its browser JavaScript and CSS. Those last two are not a documented API: re-check them after an upgrade.

---

## Style System Hierarchy

```
Theme (session-wide, least specific)
  -> Advanced Stylesheet (optional project stylesheet.css)
    -> Style Classes (project resources, reusable)
      -> Inline component styles (most specific)
```

Use themes for global defaults, style classes for reusable patterns, and inline styles only for one-off overrides. Inline properties override a class on the same component. The Advanced Stylesheet sits between theme and classes **[IA docs]**; the Gateway serves it at the top of the style-class CSS file **[live 8.3.9]**.

---

## Themes

The active theme is set by `session.props.theme`. Built-in themes:

| Kind | Themes | Can you edit it? |
|---|---|---|
| Base | `light`, `dark` | **No.** They are system config resources. Override them with an `overrides-light` / `overrides-dark` theme resource |
| Derived | `light-warm`, `light-cool`, `dark-warm`, `dark-cool` | Yes, but edits persist through upgrades and block IA's updates to that theme. Prefer a custom theme |

**ISA-101 note:** none of the built-in themes gives the neutral gray (`#808080` to `#888888`) a high performance HMI needs. Use a custom or overrides theme plus style classes.

> In 8.1 theme files lived in a Gateway data folder and were overwritten on restart. In 8.3 themes are Gateway config resources in the `core` collection, managed on disk or through the Gateway REST API.

### Overriding a base theme
Create a theme resource named `overrides-light` (or `overrides-dark`). When it exists, Ignition redirects the base theme's entry point to it. Its `index.css` imports the base theme and then adds your variables:

```css
@import "../light/index.css";
:root {
  --isa-background: #888888;
  --isa-panel: #808080;
  --isa-fault: #CC0000;
  --isa-warning: #FFAA00;
  --isa-normal: #808080;
}
```

An overrides theme has `isPrivate: true` in its `config.json`, so it does not appear in the theme list.

### Creating a custom theme on disk
1. Create `data/config/resources/core/com.inductiveautomation.perspective/themes/<theme-name>/`.
2. Add `config.json` (holds `entrypoint`, default `index.css`, and `isPrivate`), `resource.json`, and the entry-point CSS. Copying an existing derived theme folder (for example `dark-cool`) is the easiest start.
3. Start from the `light` base rules. Any rule missing from a custom theme shows up as a missing style (for example, a button without a border).
4. Put `@import` statements at the top of each CSS file, with a relative path and a closing semicolon; malformed imports may be ignored.
5. Rescan config so the Gateway loads the files: Scan File System in the Gateway web UI (Platform > System > Modes scans all config) or `POST /data/api/v1/scan/config`. `system.project.requestScan()` only scans projects and will not pick up themes.
6. Set `session.props.theme` to the new name.

Themes can also be created through the Gateway REST API (`/data/api/v1/resources/com.inductiveautomation.perspective/themes`, see the Gateway's `/openapi`). Commit theme folders with the rest of the Gateway config; see `../../ignition-config/SKILL.md`.

### Theme files on disk and how they are served [live 8.3.9]

- A hand-written `resource.json` is accepted by a config scan and not rewritten: `{"scope": "G", "description": "...", "version": 1, "restricted": false, "overridable": true, "files": ["config.json", "index.css", ...], "attributes": {}}`. List every file of the theme in `files`. `config.json` is `{"entrypoint": "index.css", "isPrivate": false}`.
- List themes with `GET /data/api/v1/resources/list/com.inductiveautomation.perspective/themes`.
- The Gateway compiles a theme into one file. It resolves the `@import` statements, strips comments, and serves the result at `/data/perspective/themes/<theme>.css`, uncompressed, with `Cache-Control: must-revalidate,no-cache,no-store`.
- Imports must be relative paths. System themes are reachable as `../light/...` and `../dark/...`, so `@import "../light/index.css";` followed by your own files gives a custom theme on the light base.
- `@property` and `@keyframes` rules pass through unchanged.
- Do not put an infinite animation of registered custom properties (`@property`) on `:root`. In Chromium it made the whole page recalculate style every frame: 60 recalculations a second, about 18 to 20 % of the main thread on a 155-node page. A keyframe animation of one element's `opacity` measured 29 recalculations in 8 s. Animate single elements through a style class instead (see Animation below).

### Built-in chrome, fonts and base variables

- The base themes style Perspective's own chrome from base variables, such as the component tooltip, the table pager, alarm table filter pills and disabled buttons **[live 8.3.9]**. For example, both base themes have `.ia_componentTooltip { background-color: var(--neutral-100); color: var(--neutral-10) }`, and on the dark scale `--neutral-100` is near-white. A custom dark palette that remaps only a few `--neutral-*` values left a near-white tooltip and grey pager blocks on a night theme. In the theme, map the whole `--neutral-*` scale and the disabled-state variables such as `--callToAction--disabled` and `--border--disabled`, or restyle `.ia_componentTooltip`. Then render-check the built-in components.
- Built-in rules read these variables **[observed in the 8.3.9 module]** (base theme CSS in the module):
  - `body`: `var(--label)` text, `var(--font-NotoSans)` font.
  - `.ia_button--primary`: background `var(--callToAction)`, text `var(--neutral-10)`, border `var(--containerBorder)`.
  - The alarm status table uses `--containerBorder` and `--callToActionHighlight`, among others.
- Fonts: the base themes' `fonts.css` registers "Noto Sans" only at weights 400, 500 and 700, from `/data/perspective/fonts/...` **[observed in the 8.3.9 module]**. `font-weight: 600` therefore renders with the 700 face, as seen in `document.fonts` **[live 8.3.9]**. Use 400, 500 and 700, or ship your own font.
- Fonts are their own Gateway config resource type, `com.inductiveautomation.perspective/fonts` **[live 8.3.9]**. The system collection holds Merriweather, NotoSans and Roboto. A font resource is a folder with `config.json` plus files named `<name>-<style>.<eot|svg|ttf|woff|woff2>`, served at `/data/perspective/fonts/<file>`.

### Choosing the session theme

- **Project default:** add `com.inductiveautomation.perspective/session-props/props.json` to the project, containing `{"custom": {}, "props": {"theme": "<theme>"}}`, with a `resource.json` whose `files` is `["props.json"]`. Then run a project scan **[live 8.3.9]**.
- **Theme from the URL (`?theme=<name>`)** **[live 8.3.9]**, useful for kiosks, bookmarks and render tests:
  - The client copies the page URL's query string into `page.props.urlParams` once, when the page starts **[observed in the 8.3.9 client]**.
  - Bind a custom property on a component in a shared dock or the page root to `try({page.props.urlParams.theme}, '')`.
  - Give that property an `onChange` script that sets `self.session.props.theme`, but only for names on an allow-list.
  - Do not use a Page Startup event for this. During startup its page object only has `pageId` and `path` (`descriptors/page_startup.json`) **[observed in the 8.3.9 module]**.
- **Theme toggle:** a button whose Gateway `script` action sets `self.session.props.theme` works **[live 8.3.9]**. The client also has a `theme` action type with config `{name}` **[observed in the 8.3.9 client]**.

---

## CSS Theme Variables

Built-in themes define their colors as CSS variables. Documented names include:

- **Neutrals:** `--neutral-10` to `--neutral-100` (in light themes, 10 is lightest; dark themes reverse the scale).
- **Status:** `--error`, `--warning`, `--warningSecondary`, `--success`, `--info`, `--infoSecondary`.
- **Other:** `--callToAction` (and `--active`, `--disabled`, `--hover` variants), `--indicator`, `--indicatorOff`, sequential `--seq-1..6`, diverging `--div-1..16`, qualitative `--qual-1..10`.

Usage:
- On a component style property, the variable name can be given directly.
- Inside a **style class**, wrap it: `var(--isa-fault)`.

ISA-101 mapping: use `--error` / `--warning` or your own `--isa-*` variables for abnormal states only. Do not use `--success` to show "running".

---

## Style Classes

Style Classes are project resources stored in the **Styles** folder of the Project Browser.

- Create: right-click Styles > New Style. Organize in subfolders: `alarms/`, `equipment/`, `layout/`, `typography/`.
- **Never use the `ia_` prefix**; it is reserved for Perspective's built-in styling and can cause unintended behavior.
- Multiple classes on one component apply in **alphabetical order**; later names override earlier ones for the same property.
- Classes support **element states** (hover, disabled and similar CSS pseudo-classes), **animations** and **media queries**.
- The optional **Advanced Stylesheet** (`stylesheet.css`, enabled by right-clicking Styles) accepts raw CSS for advanced cases.
- **A style class must be a leaf** **[live 8.3.9]**. If a folder is itself a class (it has its own `style.json` and `resource.json`) and also holds child classes, the Gateway compiles the parent and silently skips every child, with no log line. For example, `layout/card` plus `layout/card/header` never emits `header`. Name the parent `layout/card/base` or use a sibling such as `layout/card-header`.
- Style classes emit only a fixed list of CSS properties. `gap`, `display`, `width`, `height` and `min-height` are silently dropped (see below).

### Style classes on disk (8.3)

```
<project>/com.inductiveautomation.perspective/style-classes/<folder>/<name>/
  style.json
  resource.json    {"scope": "G", "version": 1, "restricted": false, "overridable": true,
                    "files": ["style.json"], "attributes": {}}
```

- Folders that only group classes need no `resource.json` **[live 8.3.9]**.
- Each path segment must match `^[a-zA-Z_][a-zA-Z0-9_\-]*$`. A legacy `data.bin` is also read **[observed in the 8.3.9 module]**.
- Run a project scan after editing on disk.

`style.json` is a base variant plus a list of variants **[live 8.3.9]**:

```json
{
  "base": {"style": {"backgroundColor": "var(--isa-panel)", "padding": "12px 16px"}},
  "variants": [
    {"pseudo": "hover", "style": {"borderColor": "var(--isa-focus)"}},
    {"media": {"feature": "maxWidth", "value": "480px"}, "style": {"padding": "8px 12px"}}
  ]
}
```

- `pseudo`: `hover`, `focus` and `disabled` were verified live. The module's `PseudoSelector` enum also has `active`, `checked`, `first-child` and others.
- `media.feature`: `minWidth`, `maxWidth`, `orientation`, `minAspectRatio`, `maxAspectRatio`, `hover` **[observed in the 8.3.9 module]**.
- `style` keys are camelCase CSS properties.
- The module's own `schemas/style-class-schema.json` describes a different, flat layout (`pseudo`, `animation`, `declarations`, `keyframes`). Do not use it for files on disk **[observed in the 8.3.9 module]**.

Generated CSS **[live 8.3.9]**:
- It is served at `/data/perspective/style-classes/<project>/<hash>/style.css`. The Advanced Stylesheet comes first (`/* BEGIN STYLESHEET */`), then the classes (`/* BEGIN STYLE CLASSES */`), sorted by their generated CSS text: static classes in class-name order, then every class whose base is animated (its CSS starts with `@keyframes`).
- Each class becomes `.psc-<path>` (the `.psc-` prefix is documented **[IA docs]**) with `/` escaped. For example `.psc-isa\/panel`, `.psc-isa\/button:hover`, or `@media (max-width: 480px) { .psc-isa\/card {...} }`. In the DOM the class attribute reads `psc-isa/panel`.
- A class name on an element does not prove the rule exists. Check the served `style.css` for the escaped selector and check the computed style (see `../../ignition-dev/references/validation-workflow.md`).
- After a class is moved or deleted, its old rule can remain in the served CSS. That is harmless while no element uses the old name.

### What a style class can emit

Only the 68 keys of the module's `StyleAttribute` enum reach the CSS **[observed in the 8.3.9 module]**. Any other key is stored in `style.json` but skipped when the CSS is written, with no warning. The keys are:

| Group | Keys |
|---|---|
| Background | `backgroundColor`, `backgroundImage`, `backgroundAttachment`, `backgroundClip`, `backgroundPosition`, `backgroundRepeat`, `backgroundSize` |
| Border | `borderColor`, `borderStyle`, `borderWidth`, `borderRadius`, `border{Top,Right,Bottom,Left}{Color,Style,Width}`, `border{Top,Bottom}{Left,Right}Radius` |
| Text | `color`, `fontFamily`, `fontSize`, `fontStyle`, `fontVariant`, `fontWeight`, `letterSpacing`, `lineHeight`, `textAlign`, `textDecoration`, `textIndent`, `textJustify`, `textOverflow`, `textShadow`, `textTransform`, `whiteSpace`, `wordSpacing`, `wordWrap`, `overflowWrap` |
| Box | `margin*`, `padding*` (shorthand and four sides), `boxShadow`, `opacity`, `cursor`, `overflow`, `overflowX`, `overflowY`, `outlineColor`, `outlineStyle`, `outlineWidth` |
| SVG | `fill`, `stroke`, `strokeWidth` |

Not emitted, among others: `display`, `gap`, `width`, `height`, `minWidth`, `minHeight`, `maxWidth`, `maxHeight`, `flex*`, `alignItems`, `justifyContent`, `position`, `zIndex`, `transform`, `transition`, `visibility`, `fontVariantNumeric`.
- Put those in the Advanced Stylesheet or on the component.
- For tabular numbers use `fontVariant: "tabular-nums"`, which the served CSS outputs as `font-variant: tabular-nums` **[live 8.3.9]**.

### Animation

```json
{"base": {"animation": {
  "duration": "2s", "delay": "0s", "direction": "normal", "iterationCount": "infinite",
  "timingFunction": "steps(1)", "fillMode": "both",
  "keyframes": {"0%": {"backgroundColor": "var(--isa-alarm)", "color": "var(--isa-on-alarm)"},
                "50%": {"backgroundColor": "var(--isa-background)", "color": "var(--isa-alarm)"},
                "100%": {"backgroundColor": "var(--isa-alarm)", "color": "var(--isa-on-alarm)"}}}}}
```

- The output is `@keyframes psc-<path>-anim` plus the class with `animation-*` properties **[live 8.3.9]**. For a variant, the name is `psc-<path>-<n>-anim` **[observed in the 8.3.9 module]**.
- **An animated variant writes no `style` block.** Repeat every static declaration (border, radius, font weight) in each keyframe **[observed in the 8.3.9 module]**. The served CSS for an animated class holds only `animation-*` properties **[live 8.3.9]**.
- Defaults when a field is missing: duration `2s`, delay `0s`, direction **`alternate`**, iterationCount `infinite`, timingFunction `linear`, fillMode `both` **[observed in the 8.3.9 module]**. Set all six. A blink needs `direction: normal` and `timingFunction: steps(1)`.
- A running CSS animation overrides normal declarations, including inline styles. An animated class therefore still shows on a component that also has inline colours **[live 8.3.9]**, as in the alarm table rows (see `perspective-components.md`).
- ISA-101: blink only for unacknowledged Critical alarms.

### Advanced Stylesheet

- Location: `<project>/com.inductiveautomation.perspective/stylesheet/stylesheet.css` plus a `resource.json` with `"files": ["stylesheet.css"]` **[live 8.3.9]**.
- Use it for what classes cannot emit, keyed on the generated class names, with `/` escaped: `.psc-layout\/card { gap: 8px; }` or `.psc-isa\/button { min-height: 48px; min-width: 48px; }`.
- Flex containers have no gap prop, so spacing between children also belongs here.
- Keep only theme variables in it (`var(--...)`), like the classes.

### Precedence between classes

- Several classes on one component apply in alphabetical order, later names winning **[IA docs]**. In the served CSS static classes are written in name order, so equal-specificity rules resolve by that order; a class with an animated base comes after all of them **[live 8.3.9]**.
- As a result, a state class often loses. For example, `isa/alarm/critical` loses to `isa/button` or `isa/text/value` on the same component. To make state and alarm classes always win, raise their specificity in the Advanced Stylesheet with a doubled selector **[live 8.3.9]**:

```css
.psc-isa\/alarm\/critical.psc-isa\/alarm\/critical {
  background-color: var(--isa-alarm);
  color: var(--isa-on-alarm);
}
```

- Built-in component classes such as `.ia_button--primary` use single-class selectors in the base themes **[observed in the 8.3.9 module]**. Style classes are served after the theme, so a class of equal specificity overrides them.

### Baseline ISA-101 classes

```
isa-background          background: var(--isa-background)   (#888888)
isa-panel               background: var(--isa-panel)        (#808080)
isa-alarm-critical      color: #CC0000; font-weight: bold   (Critical priority)
isa-alarm-high          color: #CC0000                      (High priority)
isa-alarm-medium        color: #FFAA00                      (Medium priority)
isa-alarm-low           color: #FFAA00                      (Low priority)
isa-normal              color: #808080                      (no color = normal)
isa-fault               color: #CC0000
isa-maintenance         color: #FFAA00
```

How Diagnostic priority alarms are presented (if at all) is decided in the alarm philosophy, with engineering review.

Blinking for unacknowledged Critical alarms can be built with a style class animation. Use it sparingly.

### Style class in view.json

```json
{
  "props": {
    "style": {
      "classes": "isa-background"
    }
  }
}
```

---

## Dynamic Styles with Expression Bindings

Bind `props.style.classes` to switch classes; do not bind raw colors.

```json
{
  "type": "expr",
  "config": {
    "expression": "if({view.params.alarmActive}, 'isa-alarm-critical', 'isa-normal')"
  }
}
```

---

## Inline Style Properties

The Style Editor groups properties into Text, Background, Margin and Padding, Border, Shape (fill, stroke for SVG) and Misc (opacity, cursor, overflow). Lengths accept any CSS unit (`px`, `em`, `rem`, `%`, `vw`, `vh`).

---

## Project Style Architecture

1. One custom or overrides theme holds all `--isa-*` variables.
2. Subfoldered style classes reference those variables.
3. Every screen root uses `isa-background`.
4. Equipment and alarm state classes are switched by expression bindings.

Changing alarm colors then means editing one variable, not hundreds of components. Any change to alarm colors or priority presentation is flagged for engineering review.

---

## Third-party design systems (example: OpenBridge)

Perspective can adopt an external design system's **look** without its code:
- **Colour tokens** become a custom Perspective theme (a folder with `config.json`, `resource.json`, `index.css`).
- **Icons** become a Perspective icon library resource (format and pitfalls: `icon-libraries.md`).
- **Components** are rebuilt as parameterized embedded views or Drawing symbols.

Web-component libraries (for example Lit) cannot run inside Perspective without a custom module built with the Ignition SDK.

OpenBridge ([openbridge.no](https://www.openbridge.no/)) is a maritime and industrial design system with an Automation Library (pumps, valves, tanks, readouts) and bright, day, dusk and night palettes. Its principles match ISA-101: neutral palettes, colour for state and alarms, brightness modes for control rooms. From npm `@oicl/openbridge-webcomponents`:
- palettes: `src/palettes/variables.css`, CSS variables per `data-obc-theme`, for example `--container-*`, `--element-*`, `--instrument-*`, `--alarm-*`;
- icons: SVG strings in `src/icons/*.ts`;
- symbols: `src/automation/`.

The public Storybook ([openbridge-storybook.web.app](https://openbridge-storybook.web.app/)) shows every component and state (about 2,000 stories, 182 under Automation). Use it as the visual reference when rebuilding symbols as Perspective views. The Figma community files are the design source but block automated access.

Licensing:
- Since 1.0.0, each release is AGPL-3.0-only for 180 days and then also Apache-2.0. JIP members can get a commercial licence earlier. Version 1.0.1 declares Apache-2.0.
- Take assets only from a release you may use, keep its licence notice, and keep design-system assets out of anything you redistribute (for example an Ignition Exchange resource) unless the licence allows it.
- Any alarm colour mapping is an alarm presentation change that needs engineering review.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/style-classes
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/style-classes#enabling-the-advanced-stylesheet
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/perspective-built-in-themes
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/creating-and-using-custom-perspective-themes
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-project/system-project-requestScan
