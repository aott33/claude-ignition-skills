# Perspective Component Reference

Applies to: Ignition 8.3.x

Quick reference for Perspective components used in industrial HMI design. Property names below were checked against the IA 8.3 component pages. Component `type` strings are deliberately not listed: copy them from a `view.json` saved by your own 8.3 Designer.

---

## Layout Containers

### Flex Container
Primary responsive layout. Use `direction` (`row` / `column`), `justify`, `alignItems`, `wrap`, and child `position` (`grow`, `shrink`, `basis`). Nest containers: the outer one sets page structure, inner ones group components.

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

**HMI use:** shift logs, downtime reasons, quality checks, batch notes. For a single critical setpoint, a Numeric Entry Field plus confirm popup is still clearer. A Form Submission handler that writes to a database uses `system.db.execUpdate` with a Named Query and full exception handling (see `../ignition-dev/SKILL.md`), and is treated like any other write for safety review.

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

### Table
Equipment lists, batch records, production summaries. Bind `data` to a Named Query through a query binding.

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

---

## View JSON Shape

Every view is a `view.json` with a sibling `resource.json`. Commit both together; a `resource.json` change without the matching `view.json` change is a review finding.

- `params`: the view's public contract; document every parameter.
- `root`: always a container, with `meta.name` of `root` and a background style class (`isa-background`).
- `custom`: view-level custom properties.
- `meta.name`: required on components referenced by scripts or message handlers.
- `position`: layout properties for the parent container.

Take component `type` strings from a Designer-saved view on your Gateway; do not invent them.

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
