# Perspective Styles, Themes, and Style Classes

Applies to: Ignition 8.3.x

Perspective styling is CSS-based. Use the style system hierarchy; never hardcode colors or sizes inline on individual components when a theme variable or style class can serve.

---

## Style System Hierarchy

```
Theme (session-wide, least specific)
  -> Style Classes (project resources, reusable)
    -> Inline component styles (most specific)
```

Use themes for global defaults, style classes for reusable patterns, and inline styles only for one-off overrides. Inline properties override a class on the same component.

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
- **Icons** become a Perspective icon library resource.
- **Components** are rebuilt as parameterized embedded views or Drawing symbols.

Web-component libraries (for example Lit) cannot run inside Perspective without a custom module built with the Ignition SDK.

OpenBridge ([openbridge.no](https://www.openbridge.no/)) is a maritime and industrial design system with an Automation Library (pumps, valves, tanks, readouts) and bright, day, dusk and night palettes. Its principles match ISA-101: neutral palettes, colour for state and alarms, brightness modes for control rooms. From npm `@oicl/openbridge-webcomponents`:
- palettes: `src/palettes/variables.css`, CSS variables per `data-obc-theme`, for example `--container-*`, `--element-*`, `--instrument-*`, `--alarm-*`;
- icons: SVG strings in `src/icons/*.ts`;
- symbols: `src/automation/`.

Licensing:
- Since 1.0.0, each release is AGPL-3.0-only for 180 days and then also Apache-2.0. JIP members can get a commercial licence earlier. Version 1.0.1 declares Apache-2.0.
- Take assets only from a release you may use, keep its licence notice, and keep design-system assets out of anything you redistribute (for example an Ignition Exchange resource) unless the licence allows it.
- Any alarm colour mapping is an alarm presentation change that needs engineering review.

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/style-classes
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/perspective-built-in-themes
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/styles/creating-and-using-custom-perspective-themes
- https://www.docs.inductiveautomation.com/docs/8.3/platform/gateway/web-interface/platform/gateway-deployment-modes
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-project/system-project-requestScan
