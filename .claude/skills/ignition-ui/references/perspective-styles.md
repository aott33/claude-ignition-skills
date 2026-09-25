# Perspective Styles, Themes, and Style Classes (8.1)

Perspective's styling system is CSS-based. Always use the style system hierarchy — never hardcode colors or sizes inline on individual components when a style class or theme variable can serve.

---

## Style System Hierarchy

Styles cascade from least to most specific. More specific always wins:

```
Built-in Theme (least specific)
  ↓ Style Classes
  ↓ Individual Component inline styles (most specific)
```

**Rule:** Use themes for global defaults → style classes for reusable patterns → inline styles only for one-off overrides.

---

## Built-In Themes

Six built-in themes control the base appearance of an entire session:

| Theme | Description |
|---|---|
| `light` | Default light theme |
| `dark` | Dark background |
| `light-warm` | Light with warm tone |
| `light-cool` | Light with cool tone |
| `dark-warm` | Dark with warm tone |
| `dark-cool` | Dark with cool tone |

**Activate via:** `session.props.theme` property in the Perspective session.

**ISA-101 note:** None of the built-in themes produce the specific neutral gray (`#808080`–`#888888`) required for High Performance HMI. Use a custom theme or style classes to enforce ISA-101 background colors.

**Never edit built-in theme files directly** — changes are overwritten on Gateway startup and moved to a backup folder on upgrade. Instead: create a custom CSS file that imports into the entry-point CSS files.

---

## CSS Theme Variables

Themes use CSS custom properties (variables). Reference them in style classes with `var()`:

### Neutral Colors
```css
--neutral-10   /* lightest */
--neutral-20
--neutral-30
--neutral-40
--neutral-50
--neutral-60
--neutral-70
--neutral-80
--neutral-90
--neutral-100  /* darkest */
```

### Status Colors (ISA-101 aligned)
```css
--error        /* red — use for Critical/Fault states */
--warning      /* yellow/amber — use for Warning states */
--success      /* use sparingly — not for "running" per ISA-101 */
--info         /* informational */
```

### Creating Custom Variables
Add to `variables.css`:
```css
--isa-background: #888888;
--isa-alarm-critical: #CC0000;
--isa-alarm-warning: #FFAA00;
--isa-normal: #808080;
```

Then reference in style classes: `backgroundColor: var(--isa-background)`

---

## Style Classes

Style Classes define reusable style rules applied to components by name. Define once, apply everywhere.

### Creating Style Classes

In Designer: right-click **Styles** folder → New Style → name it → configure properties → save.

**Naming rules:**
- Avoid the `ia_` prefix — reserved for built-in Perspective styles; using it causes undefined behavior
- Use descriptive names: `isa-gray-background`, `alarm-critical`, `equipment-card`
- Organize into subfolders: `alarms/`, `equipment/`, `layout/`, `typography/`

### Applying Style Classes

In a component's Style property → `classes` field → select from dropdown. Multiple classes can be applied to a single component; conflicts resolved alphabetically (later class wins).

### Standard ISA-101 Style Classes to Create

Every Ignition Perspective project should define these baseline classes:

```
isa-background          background: #888888  (standard gray)
isa-panel               background: #808080  (slightly darker panel)
isa-alarm-critical      color: #CC0000, font-weight: bold  (Priority 1)
isa-alarm-high          color: #CC0000  (Priority 2)
isa-alarm-medium        color: #FFAA00  (Priority 3)
isa-alarm-low           color: #FFAA00  (Priority 4)
isa-normal-state        color: #808080  (no color = normal)
isa-fault-state         color: #CC0000
isa-maintenance-state   color: #FFAA00
```

### Style Class in view.json

```json
{
  "type": "ia.container.flex",
  "props": {
    "style": {
      "classes": "isa-background"
    }
  }
}
```

---

## Inline Style Properties

Available in the Style Editor organized by category:

| Category | Properties |
|---|---|
| **Text** | font-family, font-size, font-weight, color, text-align, text-transform |
| **Background** | background-color, background-image, background-size |
| **Margin/Padding** | margin-top/right/bottom/left, padding-top/right/bottom/left |
| **Border** | border-style, border-width, border-color, border-radius |
| **Shape** | fill, stroke, stroke-width (SVG components) |
| **Misc** | opacity, cursor, overflow, overflow-x, overflow-y |

CSS lengths default to pixels but support all CSS units: `px`, `pt`, `em`, `rem`, `%`, `vw`, `vh`.

---

## Expression Binding with Style Variables

Use expression bindings to apply dynamic styles based on tag values:

```json
{
  "type": "expr",
  "config": {
    "expression": "if({value} >= 80, '#CC0000', '#808080')"
  }
}
```

Or reference a style class dynamically:
```json
{
  "type": "expr",
  "config": {
    "expression": "if({view.params.alarmActive}, 'isa-alarm-critical', 'isa-normal-state')"
  }
}
```

---

## Project-Level Style Architecture

For a consistent project:

1. **`variables.css`** — define all custom CSS variables (colors, spacing)
2. **Subfoldered style classes** — `alarms/`, `equipment/`, `navigation/`, `typography/`
3. **Base layout class** — all screens inherit the same gray background via style class, not inline
4. **Equipment state classes** — one class per state (normal/fault/maintenance/running) applied via expression binding

This means changing the project's alarm colors requires editing one style class, not hundreds of components.
