# Goal: Lock App to Portrait Mode

> **Pre-requisite:** Read and follow all rules in `prompts/overview.md` before starting.

---

## Objective

Lock the app to portrait orientation on both iPhone and iPad. The Xcode General tab checkboxes alone are not sufficient — `Info.plist` must explicitly declare the supported orientations.

The user will handle the Xcode General tab (Device Orientation checkboxes). Only make the code changes below.

---

## Exact Changes Required

### `warnabrotha/warnabrotha/Info.plist`

Add two keys inside the root `<dict>`:

**iPhone** — portrait only:
```xml
<key>UISupportedInterfaceOrientations</key>
<array>
    <string>UIInterfaceOrientationPortrait</string>
</array>
```

**iPad** — portrait + upside-down portrait:
```xml
<key>UISupportedInterfaceOrientations~ipad</key>
<array>
    <string>UIInterfaceOrientationPortrait</string>
    <string>UIInterfaceOrientationPortraitUpsideDown</string>
</array>
```

These keys are not present in the file yet — add them. Do not remove or modify any existing keys.

---

## Rules

- No Swift code changes required — Info.plist only.
- Do not commit to git without permission.
