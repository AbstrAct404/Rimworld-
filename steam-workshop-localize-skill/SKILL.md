---
name: steam-workshop-localize
description: Upload and verify Steam Workshop item content and localized title/description metadata without launching the game. Use when Codex needs to publish or update Workshop items with SteamCMD, write a specific Steam language branch such as Simplified Chinese (`schinese`), synchronize metadata across languages, diagnose why localized Workshop text was written to English, or verify localized metadata through Steamworks.
---

# Steam Workshop Localize

Use SteamCMD for item files and default-language metadata. Use the bundled
Steamworks client for localized title and description branches.

## Safety and prerequisites

- Confirm the exact App ID and Published File IDs before writing.
- Require Steam to be running and logged into an account that owns the items.
- Keep credentials out of scripts, manifests, console output, and source control.
- Preserve the existing English/default branch unless the user explicitly asks
  to replace it. Steam uses English as the fallback language.
- Treat Workshop uploads as external writes. Obtain any required approval before
  running the upload.

## Choose the upload path

### Content files or default metadata

Use SteamCMD `workshop_build_item <manifest.vdf>`.

A standard manifest contains:

```vdf
"workshopitem"
{
    "appid"              "294100"
    "publishedfileid"    "1234567890"
    "contentfolder"      "D:/Mods/Example"
    "previewfile"        "D:/Mods/Example/About/Preview.png"
    "title"              "Example title"
    "description"        "Example description"
    "changenote"         "Update note"
}
```

Write real line breaks inside `description`. Do not write literal `\n`.

### Localized title and description

Do not rely on a `"language"` key in a SteamCMD Workshop VDF. SteamCMD may
silently accept the manifest while still writing title and description to the
default English branch.

Use `scripts/SteamWorkshopLocalizer` instead. It calls:

1. `SteamUGC.StartItemUpdate`
2. `SteamUGC.SetItemUpdateLanguage`
3. `SteamUGC.SetItemTitle`
4. `SteamUGC.SetItemDescription`
5. `SteamUGC.SubmitItemUpdate`
6. A localized query with `SteamUGC.SetLanguage` for exact read-back validation

The tool reads `publishedfileid`, `title`, and `description` from existing VDF
manifests. It does not upload the content folder or preview image.

## Select the language keyword

Pass the Steamworks C++ API language code, not a locale or Web API code:

```powershell
dotnet .\SteamWorkshopLocalizer.dll `
  --appid 294100 `
  --language schinese `
  C:\path\item.vdf
```

Examples:

- Simplified Chinese: `--language schinese`
- Traditional Chinese: `--language tchinese`
- English: `--language english`
- Japanese: `--language japanese`
- Korean: `--language koreana`
- Brazilian Portuguese: `--language brazilian`
- Latin American Spanish: `--language latam`

Read [references/language-codes.md](references/language-codes.md) for the full
mapping. Never pass `zh-CN`, `zh-TW`, `pt-BR`, or `es-419` to
`SetItemUpdateLanguage`; those are Web API codes.

## Build the bundled client

Locate these files from the game installation or Steamworks SDK:

- `com.rlabrecque.steamworks.net.dll`
- `steam_api64.dll`

Build with explicit paths:

```powershell
dotnet build .\scripts\SteamWorkshopLocalizer\SteamWorkshopLocalizer.csproj `
  -c Release `
  /p:SteamworksManagedPath="D:\...\com.rlabrecque.steamworks.net.dll" `
  /p:SteamApiPath="D:\...\steam_api64.dll"
```

Run from the build output directory. The client writes the selected App ID to
`steam_appid.txt` beside the executable before initializing Steamworks.

For several items, pass all VDF paths in one invocation. A successful item must
end with:

```text
OK <published-file-id> language=<language> verified=true
```

Do not report success from the submit callback alone. Require the localized
read-back comparison to pass for both title and full description.

## End-to-end workflow

1. Validate App ID, Published File IDs, VDF encoding, titles, and descriptions.
2. Upload content/default metadata through SteamCMD when needed.
3. Build the Steamworks localizer once.
4. Run it with the requested API language keyword and all target VDF files.
5. Require `verified=true` for every item.
6. Optionally compare public pages using `?l=<language>` after Steam caching
   clears, but do not substitute a public-page check for API read-back.
7. Report counts, failed IDs, target language, and whether content files were
   uploaded or only localized metadata changed.

## Troubleshooting

- `SteamAPI.Init failed`: start Steam, use the owning account, confirm the App ID,
  and run the correct architecture.
- `SetItemUpdateLanguage returned false`: check the API language keyword.
- Submit succeeds but localized query differs: SteamCMD likely wrote the default
  branch, or the wrong language code was used. Retry with the bundled client.
- `EResult` is not `OK`: stop and report the exact result; do not claim success.
- Legal agreement required: stop and ask the user to accept it in Steam.
- HTTP 429 from a public Workshop page: rely on Steamworks localized query
  verification and retry the public page later.
