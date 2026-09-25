# Releasing IPFS Opener

How to produce the signed, notarized DMG and publish a release. Maintainer reference.

## Identity

Everything ships under **Queueue Studios LLC** — Apple team `J87JRCN9RM`, GitHub org `queueue-studios` (publishing as the `queueue-dev` user).
`scripts/build_release.sh` already defaults to the Queueue Studios signing identity.

## One-time setup

- A **Developer ID Application** certificate for Queueue Studios LLC in your login keychain.
- Stored `notarytool` credentials (an app-specific password from
  [appleid.apple.com](https://appleid.apple.com) → Sign-In and Security → App-Specific Passwords):

  ```bash
  xcrun notarytool store-credentials "ipfs-opener" \
    --apple-id "<your Queueue Studios Apple ID>" \
    --team-id J87JRCN9RM \
    --password "<app-specific password>"
  ```

## Build

```bash
./scripts/build_release.sh
```

> ⚠️ **Run this in a foreground Terminal** (a logged-in GUI session). The DMG window styling
> drives Finder via AppleScript and won't apply from a headless or background process — the
> script aborts if the `.DS_Store` styling didn't take, rather than shipping an unstyled DMG.
>
> The styling step also re-applies the window bounds and reads them back (Finder on macOS 27
> sometimes ignores the first `set bounds`, which shipped a 920×464 window in v1.0.2), and
> `scripts/verify_dmg_layout.py` then checks the recorded `.DS_Store` — window size, hidden
> toolbar/status bar, icon size, background, icon positions — before the DMG is signed.
>
> Note: on macOS 27 the **path bar and status bar follow the viewer's global Finder settings**
> (View menu). A DMG can't hide them, so if you see one at the bottom of the install window,
> that's your Finder preference, not a broken build.

The script: archives (Universal, Hardened Runtime) → exports a Developer ID app → notarizes
& staples the **app** (round 1, so the copied-out app passes Gatekeeper offline) → builds the
styled DMG (background art, 128-pt icons, custom volume icon) → signs it → notarizes & staples
the **DMG** (round 2) → runs a Gatekeeper check.

Output: **`build/IPFS Opener.dmg`**

Override defaults via environment variables if needed:
`SIGN_IDENTITY`, `TEAM_ID`, `NOTARY_PROFILE`, `SKIP_NOTARIZE=1` (to build without notarizing).

Styled-DMG assets live in `packaging/` (`installer_background.png`, `VolumeIcon.icns`) and are
picked up automatically.

## Verify

```bash
spctl -a -vvv --type install "build/IPFS Opener.dmg"   # should report: accepted, Developer ID
stapler validate "build/IPFS Opener.dmg"
```

Ideally, also open the DMG on a Mac that has never seen the signing cert to confirm Gatekeeper
lets it through cleanly.

## Publish

Bump `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` in the Xcode project, tag, and attach the
DMG to a GitHub Release (as `queueue-dev`):

```bash
gh release create v1.0.0 "build/IPFS Opener.dmg" \
  --title "IPFS Opener 1.0.0" \
  --notes "First release."
```
