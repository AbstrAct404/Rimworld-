# Steamworks language keywords

Use the `API language code` value with the client-side Steamworks methods
`SetItemUpdateLanguage` and `SetLanguage`. Web API codes are shown only to
prevent mixing the two formats.

| Language | API language code | Web API code |
|---|---|---|
| Arabic | `arabic` | `ar` |
| Bulgarian | `bulgarian` | `bg` |
| Chinese (Simplified) | `schinese` | `zh-CN` |
| Chinese (Traditional) | `tchinese` | `zh-TW` |
| Czech | `czech` | `cs` |
| Danish | `danish` | `da` |
| Dutch | `dutch` | `nl` |
| English | `english` | `en` |
| Finnish | `finnish` | `fi` |
| French | `french` | `fr` |
| German | `german` | `de` |
| Greek | `greek` | `el` |
| Hungarian | `hungarian` | `hu` |
| Indonesian | `indonesian` | `id` |
| Italian | `italian` | `it` |
| Japanese | `japanese` | `ja` |
| Korean | `koreana` | `ko` |
| Malay | `malay` | `ms` |
| Norwegian | `norwegian` | `no` |
| Polish | `polish` | `pl` |
| Portuguese | `portuguese` | `pt` |
| Portuguese (Brazil) | `brazilian` | `pt-BR` |
| Romanian | `romanian` | `ro` |
| Russian | `russian` | `ru` |
| Spanish (Spain) | `spanish` | `es` |
| Spanish (Latin America) | `latam` | `es-419` |
| Swedish | `swedish` | `sv` |
| Thai | `thai` | `th` |
| Turkish | `turkish` | `tr` |
| Ukrainian | `ukrainian` | `uk` |
| Vietnamese | `vietnamese` | `vi` |

Source: Steamworks documentation, “Languages Supported on Steam”:
https://partner.steamgames.com/doc/store/localization/languages

Notes:

- Steamworks client APIs use `schinese`, `tchinese`, `koreana`, `brazilian`,
  and `latam`; these are intentional and must not be “corrected” to locale codes.
- English is Steam's fallback language.
- Languages listed by Steam as game-only languages are not supported by these
  Steamworks localization APIs.
