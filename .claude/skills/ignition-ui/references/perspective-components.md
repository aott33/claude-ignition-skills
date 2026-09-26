# Perspective Component Reference

Applies to: Ignition 8.3.x

Quick reference for Perspective components used in industrial HMI design. Property names below were checked against the IA 8.3 component pages. This file does not catalogue component `type` strings (a few appear as examples). Copy them from a `view.json` saved by your own 8.3 Designer, or read them from the Perspective module on your Gateway (next section). Never guess them.

Labels on the 8.3.9 notes below: **[IA docs]** from the IA 8.3 manual; **[live 8.3.9]** verified on a live 8.3.9 Gateway (see the repository's `docs/verification.md`); **[observed in the 8.3.9 client]** / **[observed in the 8.3.9 module]** read from Perspective's browser JavaScript and CSS or from the module's Java classes and bundled files. The observed items are not a documented API, so re-check them after an upgrade.

---

## Component IDs and schemas come from the module

The authoritative component list, with every prop and its schema default, ships inside the Perspective module:
- The built-in modules sit in `/usr/local/bin/ignition/user-lib/modules` in the Docker image **[IA docs]**. The Perspective module file is `Perspective-module.modl`, a zip archive.
- Inside it, `perspective-common-<version>.jar` holds **[observed in the 8.3.9 module]**:
  - `ia.components.json`: 70 components in 8.3.9, each with `id` (the view.json `type`), `schema` (props and defaults) and `childPositionSchema`;
  - more `*.components.json` files for the chart, map, barcode and PDF components;
  - `schemas/`: binding, transform, style, `session-props` and `view-props` schemas;
  - `descriptors/`: the objects that event scripts receive.
- Extraction steps: `../../ignition-dev/references/validation-workflow.md`.

Examples of 8.3.9 ids: `ia.container.flex`, `ia.container.coord`, `ia.display.label`, `ia.display.icon`, `ia.display.view` (Embedded View), `ia.display.flex-repeater`, `ia.display.table`, `ia.display.alarmstatustable`, `ia.display.linear-scale`, `ia.input.button`.

The Gateway deep-merges each component's schema defaults under the props you write (`ComponentModel` merges `ComponentDescriptor.defaultProperties()`) **[observed in the 8.3.9 module]**, so any prop you leave out, even a nested key, takes its schema default **[live 8.3.9]** (see Alarm Status Table `rowStyles`). Check the `ia.components.json` defaults for anything you omit: some carry hard-coded colours.

---

## Layout Containers

### Flex Container
Primary responsive layout. Use `direction` (`row` / `column`), `justify`, `alignItems`, `wrap`, and child `position` (`grow`, `shrink`, `basis`). Nest containers: the outer one sets page structure, inner ones group components.

8.3.9 details:
- **No `gap` prop.** The props are `direction`, `wrap`, `justify`, `alignItems`, `alignContent` and `style` **[observed in the 8.3.9 module]**. Space children with a `gap` rule in the Advanced Stylesheet keyed on the container's class **[live 8.3.9]**, or with child margins.
- `direction`, `wrap`, `justify`, `alignItems` and `alignContent` are written as inline styles **[observed in the 8.3.9 client]**. A style class cannot turn wrapping on, so set `props.wrap = "wrap"`.
- Child `position` keys are `grow`, `shrink`, `basis`, `align` and `display` **[observed in the 8.3.9 module]**. Nothing else is added: no `min-width` or `overflow` **[observed in the 8.3.9 client]**. For a text child that should shrink and show an ellipsis, set `minWidth: 0` in its style.
- Hide a child with a binding on `position.display` (boolean) **[live 8.3.9]**.

### Breakpoint Container
Separate child layouts at defined widths. Use when one view must serve control room monitors, tablets and phones.

### Coordinate Container
Fixed-position layout for P&ID graphics and equipment diagrams. Children do not reflow.

### Tab Container
Switchable panels for related content (Status | Trends | Alarms | Configuration). Each tab usually holds an Embedded View.

---

## Drawing Component (new in 8.3) - SVG symbols

A component for SVG vector graphics that you create and edit inside the Designer with the built-in **Drawing Editor** (right-click the component, **Edit Drawing**; only one drawing can be open at a time). SVG files can be imported by drag and drop into the editor.

**Key props:** `viewBox`, `preserveAspectRatio` (default centers and keeps aspect ratio), `elements` (the SVG element tree as JSON), `style`. Each element carries camel-cased SVG attributes such as `fill`, `stroke`, `opacity`, `transform`, `visibility`, `style`, `name` (label in the editor's Layers panel) and `id`. IA notes that some SVG attributes were adapted for Ignition; test them before relying on them.

**ISA-101 symbol library pattern:**
1. Draw or import each symbol (pump, valve, motor, vessel) once, gray by default.
2. Wrap each drawing in a small view with a parameter contract (`tagBasePath`, `state`).
3. Drive abnormal appearance with expression bindings on the relevant element properties (for example `fill` or `visibility`), keeping color values in theme variables or style classes instead of scattering hex codes.
4. Reuse the wrapped view with Embedded View or Flex Repeater, and attach a drop configuration so dragging a UDT instance creates a bound symbol.
5. Keep symbols static: no decorative animation, gradients or 3D shading.

The built-in symbol components (Motor, Pump, Valve, Vessel, Sensor) still exist; use the Drawing component when the plant needs its own symbol set.

---

## Form Component (new in 8.3) - operator data entry

A container for validated, responsive input forms (text, number, dropdown, checkbox, radio and other widget types).

**Key props:** `name` (used by handlers to identify submissions), `disabled`, `readOnly`, `columns` (columns > rows > widgets), `actions` (Submit and Cancel), `data` (entered values keyed by widget id), `validation` (read-only live results).

**Rules to design around:**
- The **Submit and Cancel buttons are always rendered**; they can be disabled but **cannot be hidden**. Do not plan a layout that assumes they can be removed.
- `actions.submit.fireComponentEvent` triggers the component's `onSubmitActionPerformed` event.
- `actions.submit.fireSubmissionEvent` sends the form data to a Gateway-scoped **Form Submission** event script named in `submissionHandler`. Create it under Project Browser > Perspective > Gateway Events. The script receives `session`, `name`, `data`, `formContext`, `sessionContext` and `retry`, and returns a response dictionary that the form displays.
- `autoDisable` disables Submit while the form is invalid or a submission is in progress; `resetOn` and `awaitResponse` control reset behavior.
- Rows support `visibleWhen` / `enabledWhen` conditions.

**HMI use:** shift logs, downtime reasons, quality checks, batch notes. For a single critical setpoint, a Numeric Entry Field plus confirm popup is still clearer. A Form Submission handler that writes to a database uses `system.db.execUpdate` with a Named Query and full exception handling (see `../../ignition-dev/SKILL.md`), and is treated like any other write for safety review.

---

## Audio Component (new in 8.3)

Plays and pauses sound clips in the browser. The UI is hidden by default (`display` shows browser-dependent controls). Key props: `source` (media URL), `play`, `loop`, `volume` (0 to 100), `playbackRate`, `allowDownload`. Supported file types depend on the browser.

**Alarm rule (engineering review required):** audible process alarms must still come from hardware annunciators (horns, stack lights, annunciator panels driven by the controller). Browser audio stops when a tab is closed, muted or blocked, so it is **not a substitute**. At most it can supplement the hardware horn; any such use goes through engineering review.

---

## Offline Mode (Perspective mobile app)

**Offline Mode only works in the Perspective App on mobile devices; it is not supported in desktop browsers.** Enable it in Project Properties > Perspective > Offline Mode (and in the app). Settings include required security levels, an authentication token expiration (default 7 days), cached themes and cached languages.

While offline:
- Tags, alarms and queries do not update; Gateway-event and database scripts do not run.
- Only views loaded earlier are available.
- The Form component queues submissions and sends them when the connection returns. Arrival order is not guaranteed, so include timestamps and design the Form Submission handler to process out-of-order and retried (`retry`) submissions.

Use it for rounds, inspections and checklists. Never design control actions or alarm response that depend on an offline session.

---

## Alarm Components (ISA-18.2)

### Alarm Status Table
Active alarm display. Configure priority, event time, source, display path, state and acknowledge. Place it in a persistent banner on every screen or on a dedicated alarm summary screen. Supports filtering by priority and state.

**Row colours (`props.rowStyles`), 8.3.9:**
- `rowStyles` has four states: `activeUnacked`, `activeAcked`, `clearUnacked` and `clearAcked`. Each has a `base` style and `priorities.{diagnostic, low, medium, high, critical}` styles.
- A row's class list is `alarmTableBodyRow`, plus the base `classes`, plus the priority `classes`. Its inline style merges the base and priority style objects **[observed in the 8.3.9 client]**.
- **An entry that sets only `classes` still gets the component's default colours inline**, and inline beats the class **[live 8.3.9]**. These are the schema defaults, for example `#DB3939` for activeUnacked, `#7C2320` for activeAcked and a solid blue `#2E5EAA` bar for clearUnacked. A cleared-unacknowledged Critical row rendered as that blue bar in both day and night themes.
- Fix: set explicit `backgroundColor` and `color` with theme variables on **every** base and priority entry of all four states, and keep the classes. For example: `"critical": {"classes": "isa/alarm/critical", "backgroundColor": "var(--isa-alarm)", "color": "var(--isa-on-alarm)"}`.
- A blinking class (a style class animation) still shows over those inline colours, because a running animation overrides inline declarations **[live 8.3.9]**.
- Row colours are alarm presentation: every mapping goes through engineering review.

**Hand-authoring the component** **[observed in the 8.3.9 module]**:
- Props you omit take their schema defaults from the Gateway.
- A column left out of `columns.active` uses its schema default `enabled` value (for example `source` true, `label` false), so list every column you rely on.
- The Display Path column shows the source path for alarms without a Display Path. The Gateway fills it from `getDisplayPathOrSource()`.

### Alarm state in bindings and scripts

- **Alarm Metrics** **[IA docs]**:
  - Syntax: `<TagPath>/Alarm Metrics.<Property>` on a tag, a folder or a UDT instance.
  - 8.3.9 adds an Alarm Metrics folder at the tag provider level. It can be bound or subscribed to, but not read directly.
  - Properties include `ActiveUnackCount`, `ActiveAckCount`, `ClearUnackCount`, `HasActive`, `HasUnacknowledged`, `HighestActivePriority`, `HighestActiveName`, `HighestUnackedPriority`, `HighestUnackedName`, `ShelvedCount`, `LastActiveTime`, and per-priority forms such as `ActiveCountCritical` and `HasActiveUnackedHigh`.
  - Live: indirect tag bindings such as `{"tagPath": "{tp}/Alarm Metrics.HighestActivePriority", "references": {"tp": "{view.params.tagPath}"}}` on UDT instances and member tags drove card alarm states correctly **[live 8.3.9]**.
- **Gateway-wide counts:** `[System]Gateway/Alarming/Active and Unacked`, `Active and Acked`, `Clear and Unacked` and `Clear and Acked` carry no priority. They work as change triggers for an `expr-struct` binding whose script transform calls `system.alarm.queryStatus` once **[live 8.3.9]**.
- **Alarm events in scripts** **[live 8.3.9]**:
  - `event.getPriority().ordinal()` is 0 (Diagnostic) to 4 (Critical); `event.isAcked()` and `event.isCleared()` also work.
  - `event.getActiveData().getTimestamp()` already returns epoch milliseconds (a Java `long`). javap of the Gateway's `common.jar` shows `EventData.getTimestamp()` returning `long`. Calling `.getTime()` on it raises an error. If a broad `except` swallows that error, the sort key is silently lost.

### Alarm Journal Table
Historical alarm events for shift handoff, troubleshooting and alarm-rate metrics.

Ignition priorities are Diagnostic, Low, Medium, High, Critical. Priority and acknowledgement changes are engineering-review items.

---

## Data Display Components

### Power Chart
Interactive historical trend: multiple pens, zoom and pan, time range selection, runtime pen configuration.

### Sparkline
Minimal line chart of recent history for one datapoint. Bind `points` to a two-column dataset (date, then number) sorted ascending by time, from a history or Named Query binding. Set `desired.high` and `desired.low` to draw the expected operating band; that band is an ISA-101 friendly way to show "in range" without color on the value.

### Linear Scale
Ticks and labels between `minValue` and `maxValue`, with `indicators` for the value, setpoint and alarm zones. Operators read deviation from analog shape faster than from a number.

8.3.9 notes **[observed in the 8.3.9 client]**:
- The scale is horizontal when the component is wider than tall, otherwise vertical.
- Its `<svg>` gets no width or height of its own, so give the component an explicit size. A 300px flex basis rendered cleanly **[live 8.3.9]**.
- Tick, label and indicator colours are applied as inline styles, so `var(--token)` values work.

### Table
Equipment lists, batch records, production summaries. Bind `data` to a Named Query through a query binding.

8.3.9 notes:
- **Body cells have no padding**: the component CSS has `.table-container .t .tc .content{padding:0px}`, while header cells have an inset. Body text touches the table edge and does not line up with the headers. Set `props.cells.style` to `{"paddingLeft": "5px", "paddingRight": "5px"}`, which matched the header inset **[live 8.3.9]**.
- A cell given as `{"value": ..., "style": {"classes": "..."}}` renders the value with that style **[live 8.3.9]**. The client accepts this form when `value` is a primitive, `null` or a date **[observed in the 8.3.9 client]**.
- A number shown as a date needs the column's `render: "date"` **[live 8.3.9]**.
- Check header titles at phone width: long titles wrap to two lines. Shorten them, or move units into the cell format.

### Label
`ia.display.label` renders as `<div class="ia_labelComponent ...">` with the text in a `<span>` **[observed in the 8.3.9 client]**. No Perspective CSS sets a label's colour or font size, so a label without classes inherits from its container.
- `alignVertical` defaults to `center` (schema, sent by the Gateway when omitted) **[observed in the 8.3.9 module]**. Set it explicitly.
- `textStyle` `whiteSpace: nowrap` with `textOverflow: ellipsis` cut the meaningful end of a message at 390px width **[live 8.3.9]**. Put the important words first, or let the text wrap.

### Icon
`ia.display.icon` with `props.path = "<library>/<name>"`. Colouring, custom libraries and failure modes: `icon-libraries.md`. A missing icon name raises a page error **[live 8.3.9]**.

---

## Equipment Symbol Components

Built-in symbols: Motor, Pump, Valve, Vessel, Sensor. Keep the normal state gray and show abnormal states through a style class switched by an expression binding:

```json
{"type": "expr", "config": {"expression": "case({view.params.state}, 2, 'isa-fault', 3, 'isa-maintenance', 'isa-normal')"}}
```

Map integer states: 0 = Stopped (gray), 1 = Running (gray), 2 = Fault (red), 3 = Maintenance (amber).

---

## Reuse and Embedding

### Embedded View
Reusable faceplate, banner or widget. Set `props.path` to the view and pass parameters in `props.params`:

```json
{
  "props": {
    "path": "Faceplates/Compressor",
    "params": {
      "equipmentId": 42,
      "tagBasePath": "[default]DairyPlant/Refrigeration/Compressor1"
    }
  }
}
```

### Flex Repeater
Creates one view instance per entry in `props.instances`, using the view at `props.path`. Each instance object holds the parameters for that instance (plus optional `instanceStyle` and `instancePosition`). Container behavior: `direction`, `wrap`, `justify`, `alignItems`, `elementStyle`, `elementPosition`.

**Data-driven pattern:** bind `instances` with a query binding to a Named Query using Return Format `json`, so each row becomes an object; name the query columns to match the card view's parameters. Add a transform if the shape needs adjusting.

8.3.9 details:
- Schema defaults are `useDefaultViewWidth: true`, `useDefaultViewHeight: true` and `elementPosition: {grow: 1, shrink: 1, basis: 0}` **[observed in the 8.3.9 module]**.
- With `useDefaultViewWidth` in a row (or `useDefaultViewHeight` in a column), each element is forced to `flex: 0 0 auto`, and `elementPosition` has no effect **[observed in the 8.3.9 client]**. For a wrapping card grid, set `useDefaultViewWidth: false` and give `elementPosition` a basis, for example `{"grow": 1, "shrink": 1, "basis": "288px"}` **[live 8.3.9]**.
- Each instance's params are the instance object without `instanceStyle` and `instancePosition`, plus `index` **[observed in the 8.3.9 client]**.
- Styles apply in this order: `elementPosition`, `elementStyle`, `instanceStyle`, `instancePosition`. The `classes` of `instanceStyle` replace the element classes **[observed in the 8.3.9 client]**.
- Embedded View and Flex Repeater render each child view inside a `div.view-parent`. The client CSS has `.view-parent{display:flex}` and `.view-parent .view{flex:1;overflow:auto}`. A view's root component renders directly, with class `view` and no wrapper **[observed in the 8.3.9 client]**.

### Drop Configuration
Set `dropConfig` on the faceplate view. `udts` associates the view with a UDT; `dataTypes` associates it with a tag data type. Each entry names a view `param` and an `action`: `bind` (tag binding to the dropped tag) or `path` (fills the param with the tag path, best for indirect bindings).

---

## Operator Interaction Components

### Button
- Minimum touch target 44 x 44 px.
- Destructive or critical actions (Emergency Stop, bypass): red, with a confirm popup.
- Disabled state clearly grayed.

Write handler with error handling (Perspective component event script body):

```python
import java.lang

logger = system.util.getLogger('HMI.StartButton')
try:
    results = system.tag.writeBlocking(['[default]Area1/Pump1/StartCmd'], [True])
    if not results[0].isGood():
        logger.warn('Start command write returned %s' % results[0])
except java.lang.Throwable as ex:
    logger.error('Start command write failed: %s' % ex)
except Exception as ex:
    logger.error('Start command write failed: %s' % ex)
```

### Numeric Entry Field
Always set min and max limits and a display format. For critical setpoints, open a confirm popup and write only from the popup's confirm button:

```python
# onActionPerformed of the entry's "Apply" button
system.perspective.openPopup(
    'confirmSetpoint',
    'Popups/ConfirmSetpoint',
    params={'tagPath': '[default]Tank1/TempSetpoint', 'newValue': self.parent.getChild('Entry').props.value}
)
```

The confirm view performs the write (with the error handling above) and calls `system.perspective.closePopup('confirmSetpoint')`. Never use `system.gui.confirm`; it is a Vision API.

### Multi-State Button / Toggle Switch
Mode selection (Hand/Off/Auto). Bind to an integer mode tag and label each state in words.

### Dropdown
Bind `options` with a query binding (Return Format `json`) to a Named Query whose columns are `value` and `label`. In script code, fetch the same data with `system.db.execQuery('Lists/Recipes', {})` inside `java.lang.Throwable` / `Exception` handling.

### Form
Multi-field operator entry; see the Form section above.

---

## Navigation Components

- **Menu Tree:** side navigation following the ISA-95 hierarchy (Site > Area > Equipment).
- **Horizontal Menu:** top-bar global navigation.
- **Link:** contextual navigation ("Open Alarm History"). Style links consistently.

Navigate in script with `system.perspective.navigate(page='/area/boilers', params={...})`.

### Page configuration and docks (on disk)

The project's `com.inductiveautomation.perspective/page-config/config.json` holds the page routes and docks. Pair it with a `resource.json` whose `files` is `["config.json"]`. The shape below worked for routes plus a shared top bar and a left navigation dock **[live 8.3.9]**:

```json
{
  "pages": {
    "/": {"title": "Overview", "viewPath": "Pages/Overview"},
    "/area/:area": {"title": "Area", "viewPath": "Pages/Area"}
  },
  "sharedDocks": {
    "cornerPriority": "top-bottom",
    "top": [{"id": "TopBar", "viewPath": "Shell/TopBar", "viewParams": {}, "size": 56,
             "show": "visible", "anchor": "fixed", "content": "push", "handle": "hide",
             "resizable": false, "modal": false, "iconUrl": "", "autoBreakpoint": 768}],
    "left": [{"id": "Nav", "viewPath": "Shell/Nav", "viewParams": {}, "size": 240,
              "show": "auto", "autoBreakpoint": 768, "anchor": "fixed", "content": "auto",
              "handle": "hide", "resizable": false, "modal": false, "iconUrl": ""}]
  }
}
```

Keys and behaviour **[observed in the 8.3.9 module and client]**:
- Page keys: `viewPath`, `title`, and optionally `docks`.
- `sharedDocks` keys: `cornerPriority` (`left-right` or `top-bottom`), `showHandleDuration` in ms, and `top`, `left`, `right`, `bottom` (lists of docks).
- Dock keys:

  | Key | Values |
  |---|---|
  | `id`, `viewPath`, `viewParams`, `size`, `resizable`, `iconUrl`, `modal`, `autoBreakpoint` | as named |
  | `show` | `visible`, `onDemand`, `auto` |
  | `anchor` | `fixed`, `scrollable` |
  | `content` | `push`, `cover`, `auto` |
  | `handle` | `show`, `hide`, `autoHide` (the older `hideHandle` key is still read) |

- Client defaults for a missing key: size 160, show `onDemand`, anchor `fixed`, content `cover`, handle `autoHide`, autoBreakpoint 600, modal false.
- A page without `docks` uses `sharedDocks`. A page's own docks are merged into the shared ones by `viewPath`.
- `show: "auto"` expands the dock when the window is at least `autoBreakpoint` wide. `content: "auto"` pushes the page at that width or wider and covers it below.
- `modal: true` draws an overlay while the dock is expanded and has focus (for example after a click inside it, or after opening it with its handle), so do not use it for a desktop navigation rail.
- Verified with `show: "auto"` and `content: "auto"` at 768: the nav rail stayed open at 1440px, and a dock `toggle` action opened it as a drawer at 390px **[live 8.3.9]**.

Page properties written by the client **[observed in the 8.3.9 client]**:
- `page.props.path`: updates on navigation.
- `page.props.primaryView`.
- `page.props.title`: from the page-config title, or the project title.
- `page.props.urlParams`: the query string as a map, written once when the page starts.
- `page.props.dimensions.viewport.width` and `.height`: the document's client width and height, rewritten on resize with a 100 ms debounce, and on scroll. Bind responsive layout to them, for example `try({page.props.dimensions.viewport.width}, 1024) < 768` **[live 8.3.9]**.
- `page.props.appBarVisible`.

### Event actions (view.json)

An action is `{"type": ..., "scope": "C" | "G", "config": {...}}`. Optional keys are `enabled`, `preventDefault`, `stopPropagation` and `permissions` **[observed in the 8.3.9 client]**.

| Scope | `type` | `config` |
|---|---|---|
| Client (`C`) | `dock` | `{id, type: open\|close\|toggle, viewParams}` |
| Client | `nav` | `{page}`, or `{view, params}`, or `{url, newTab}`; also `relativeNavigationIndex` |
| Client | `theme` | `{name}` (sets `session.props.theme`) |
| Client | `popup`, `alter-dock`, `fullscreen`, `login`, `logout`, `refresh`, `request-print`, `console-log` | see a Designer-saved view |
| Gateway (`G`) | `script` | `{script}`: the body of `runAction(self, event)` |
| Gateway | `auth-challenge` | see a Designer-saved view |

`dock` with `toggle`, `nav` with `page`, and `script` were used in a verified project **[live 8.3.9]**. For the other types, copy the `config` shape from a Designer-saved view.

---

## View JSON Shape

Every view is a `view.json` with a sibling `resource.json`. Commit both together; a `resource.json` change without the matching `view.json` change is a review finding.

- `params`: the view's public contract; document every parameter.
- `root`: always a container, with `meta.name` of `root` and a background style class (`isa-background`).
- `custom`: view-level custom properties.
- `meta.name`: required on components referenced by scripts or message handlers.
- `position`: layout properties for the parent container.

Take component `type` strings from a Designer-saved view on your Gateway or from the module's `ia.components.json`; do not invent them.

Keys the 8.3.9 module reads **[observed in the 8.3.9 module]**:
- View: `root`, `props`, `custom`, `params`, `events`, `permissions`, `propConfig`.
- Component: `version`, `type`, `props`, `custom`, `meta`, `position`, `events`, `propConfig`, `scripts`, `children`.
- A `propConfig` entry (keyed by property path, such as `props.text`, `custom.x` or `params.tagPath`): `binding`, `persistent`, `paramDirection`, `onChange` (`{script, enabled}`), `access`.
- `meta.domId` sets the element's DOM `id`, which gives render tests stable selectors such as `#MenuToggle` **[live 8.3.9]**.

Binding `type` ids **[observed in the 8.3.9 module]**:

| `type` | `config` keys (module schemas) |
|---|---|
| `tag` | `tagPath`, `mode` (`direct`, `indirect`, `expression`), `references`, `bidirectional` |
| `expr` | `expression` |
| `expr-struct` | `struct` (name to expression), `waitOnAll` |
| `property` | `path`, `bidirectional` |
| `query` | `queryPath`, `returnFormat`, `parameters`, `polling`, ... |
| `tag-history` | `tags`, `dateRange`, `returnFormat`, `aggregate`, ... |
| `http` | `request`, `polling`, ... |

- Transform types are `expression`, `script`, `map` and `format` **[observed in the 8.3.9 module]**.
- A `script` transform stores its body under `code`. The Gateway wraps it in `def transform(self, value, quality, timestamp):` **[observed in the 8.3.9 module]**.
- An `onChange` script is the body of `valueChanged(self, previousValue, currentValue, origin, missedEvents)` **[observed in the 8.3.9 module]**.
- A `script` action is the body of `runAction(self, event)` **[observed in the 8.3.9 module]**.
- `tag`, `expr`, `expr-struct`, `property`, script transforms and `onChange` scripts were all used in a verified project **[live 8.3.9]**.

---

## Sources

- https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-display-palette/perspective-drawing
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-input-palette/perspective-form
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-display-palette/perspective-audio
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/perspective-sessions/ignition-perspective-app/offline-mode
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/scripting-in-perspective/perspective-session-events-scripts
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-embedding-palette/perspective-flex-repeater
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-embedding-palette/perspective-embedded-view
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-display-palette/perspective-sparkline
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/components/perspective-components/perspective-display-palette/perspective-linear-scale
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/working-with-perspective-components/bindings-in-perspective/query-bindings-in-perspective
- https://www.docs.inductiveautomation.com/docs/8.3/ignition-modules/perspective/working-with-perspective-components/bindings-in-perspective/tag-bindings-in-perspective/drop-configuration
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execQuery
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-db/system-db-execUpdate
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-perspective/system-perspective-openPopup
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-perspective/system-perspective-closePopup
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-perspective/system-perspective-navigate
- https://www.docs.inductiveautomation.com/docs/8.3/appendix/scripting-functions/system-tag/system-tag-writeBlocking
- https://www.docs.inductiveautomation.com/docs/8.3/tutorials/version-control-guide/best-practices-for-team-environments
- https://www.docs.inductiveautomation.com/docs/8.3/platform/tags/tag-properties/tag-alarm-properties (Alarm Metrics)
- https://www.docs.inductiveautomation.com/docs/8.3/platform/advanced-deployments/docker-image (built-in module folder)
