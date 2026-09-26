# Perspective Icon Libraries

Applies to: Ignition 8.3.x

How to add a custom SVG icon library for the Icon component, and the pitfalls that make icons render blank.

Labels: **[live 8.3.9]** verified on a live 8.3.9 Gateway (see the repository's `docs/verification.md`); **[observed in the 8.3.9 client]** / **[observed in the 8.3.9 module]** read from Perspective's browser JavaScript or from the module's bundled files, not a documented API (re-check after an upgrade); **[tested in Chromium]** reproduced in headless Chromium outside Perspective.

---

## Resource layout [live 8.3.9]

An icon library is **Gateway config**, not a project resource:

```
data/config/resources/<collection>/com.inductiveautomation.perspective/icons/<library>/
  config.json      {"svgFileName": "<library>.svg"}
  resource.json    {"scope": "G", "version": 1, "restricted": false, "overridable": true,
                    "files": ["config.json", "<library>.svg"], "attributes": {}}
  <library>.svg
```

- Load or reload it with a config scan (`POST /data/api/v1/scan/config`). It is Gateway config, so `system.project.requestScan()` does not cover it.
- `GET /data/api/v1/resources/names/com.inductiveautomation.perspective/icons` lists it with `"modes": ["core"]`. The built-in libraries show `["system"]`.
- The built-in libraries in 8.3.9 are `material`, `ignition`, `symbol_mimic`, `symbol_simple` and `symbol_p&id` **[observed in the 8.3.9 module]** (`perspective-icons` jar). Use `material.svg` as the format reference.
- Reference an icon from `ia.display.icon` as `props.path = "<library>/<name>"`.
- The client fetches `GET /data/perspective/icons/<library>.svg`, optionally with `?digest=<asset digest>`. The response needs no auth, carries a `perspective-asset-digest` header, is not gzipped and has no `Cache-Control`.

## Sprite format [observed in the 8.3.9 client]

Copy the layout of the built-in `material.svg`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <defs><style>.icon { display: none } .icon:target { display: inline }</style></defs>
  <svg viewBox="0 0 24 24">
    <g class="icon" id="pump"><path d="..."/></g>
  </svg>
  <svg viewBox="0 0 36 36">
    <g class="icon" id="valve"><path d="..."/></g>
  </svg>
</svg>
```

- The client parses the whole file with `innerHTML` and treats every innermost element with a `viewBox` as one icon.
- The icon name is that element's `id`, or else its first child's `id`. So `<g class="icon" id="NAME">` must be the **first child** of each nested `<svg viewBox>`.
- `viewBox` values are read with `parseInt`, so use integers.
- Leave foreground shapes **without a `fill` attribute**, as `material.svg` does, so they inherit the fill Perspective sets on the outer `<svg>` (see Colour below). A literal `fill="currentColor"` on a shape ignores the component's `color` prop. A stroke-only shape with `stroke="currentColor"` follows CSS `color` (style classes) but not the `color` prop.
- Keep every `id` unique across the library, for example by namespacing mask and clip ids per icon. Icons render inline, so ids share one page.
- `material.svg` rounds coordinates to 2 decimals **[observed in the 8.3.9 module]**. Doing the same cut a 1,969-icon library from 2.34 MB to 1.83 MB, and pixel comparisons in the verified project (the repository's `docs/verification.md`) showed no visible change.

## Colour [observed in the 8.3.9 client]

- The Icon component renders `<svg viewBox="..." style="fill: <colour>" data-icon="<library>/<name>">` with the icon inline.
- `<colour>` is `props.style.fill`, else `props.color`, else `currentColor`.
- Perspective always writes that fill inline, so a style class that sets `fill` loses.
- **To colour icons from a style class, set CSS `color` in the class** and leave `props.color` and `props.style.fill` empty. In the verified project the icon classes set both `color` and `fill`, and icons took the class `color` **[live 8.3.9]**.
- `props.color` accepts a theme variable, for example `var(--isa-fault)`. The client also turns a bare `--name` into `var(--name)` **[observed in the 8.3.9 client]**.
- Pick a text or foreground token for icon colour, never a background token.
- Icon colour for alarm state is alarm presentation: it follows the ISA-101 rules and needs engineering review like any other alarm colour.

## Failure modes

| Symptom | Cause | Source |
|---|---|---|
| Icon renders empty and the page reports `React.cloneElement(...): The argument must be a React element, but you passed null` (from `IconRenderer.handleParsedAndCachedValueReady`) | The name in `props.path` is not in the library, for example a typo | **[live 8.3.9]** |
| Possible, not reproduced: icons stay blank after adding a very large library | The client caches every icon's `outerHTML` in `sessionStorage` under `<library>\|<name>` plus `icon_library\|<library>`, and the library digest in `localStorage` key `assetDigests/icon`. The `sessionStorage` writes are not guarded (the digest write is). One `sessionStorage` quota (about 5.2 million characters in Chromium) is shared by all libraries. A quota error is thrown inside an async handler with no catch, so expect an "Uncaught (in promise)" `QuotaExceededError` in the console | **[observed in the 8.3.9 client]**. For scale: `material` plus a 1,969-icon library used 2.54 million characters **[live 8.3.9]** |
| A masked icon draws without its cut-out, or its masked part disappears | Inline SVG ids are page-global. If the first copy of a mask id in the DOM is under `display:none` (for example a hidden component), Chromium renders the other copies without the mask. If the first copy is under `visibility:hidden`, the masked content disappears unless the `<mask>` has `visibility="visible"` | **[tested in Chromium]** |

How to avoid them:
- Put a render check with a page-error listener in the validation run. It catches a wrong icon name immediately (see `../../ignition-dev/references/validation-workflow.md`).
- When a library is large, ship only the icons the project uses.
- Prefer icons without masks. Where you can, redraw a knock-out as one id-free even-odd path. Where a mask is unavoidable:
  - set `visibility="visible"` on the `<mask>`;
  - do not hide other copies of that icon with `display:none`: change the icon path or unmount the component instead.

## Licensing

Icons from a third-party design system keep that project's licence. Keep its notice with the library and check the licence before redistributing (see the OpenBridge note in `perspective-styles.md`).
