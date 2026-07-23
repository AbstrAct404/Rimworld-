using System.Text.RegularExpressions;
using Steamworks;

uint appId = 294100;
string language = "schinese";
var manifests = new List<string>();
for (int i = 0; i < args.Length; i++)
{
    switch (args[i])
    {
        case "--appid" when i + 1 < args.Length:
            appId = uint.Parse(args[++i]);
            break;
        case "--language" when i + 1 < args.Length:
            language = args[++i];
            break;
        default:
            manifests.Add(args[i]);
            break;
    }
}

if (manifests.Count < 1)
{
    Console.Error.WriteLine(
        "Usage: SteamWorkshopLocalizer [--appid 294100] " +
        "[--language schinese] <vdf> [<vdf> ...]"
    );
    return 2;
}

File.WriteAllText(Path.Combine(AppContext.BaseDirectory, "steam_appid.txt"), appId.ToString());

if (!SteamAPI.Init())
{
    Console.Error.WriteLine("SteamAPI.Init failed. Ensure Steam is running and the account owns RimWorld.");
    return 3;
}

try
{
    foreach (string manifestPath in manifests)
    {
        var item = ReadManifest(manifestPath);
        Console.WriteLine($"START {item.PublishedFileId} {item.Title}");

        UGCUpdateHandle_t handle = SteamUGC.StartItemUpdate(
            new AppId_t(appId),
            new PublishedFileId_t(item.PublishedFileId)
        );

        if (!string.IsNullOrWhiteSpace(item.ContentFolder))
        {
            if (!Directory.Exists(item.ContentFolder))
                throw new DirectoryNotFoundException(
                    $"Content folder does not exist: {item.ContentFolder}"
                );
            Require(SteamUGC.SetItemContent(handle, item.ContentFolder), "SetItemContent");
        }
        Require(SteamUGC.SetItemUpdateLanguage(handle, language), "SetItemUpdateLanguage");
        Require(SteamUGC.SetItemTitle(handle, item.Title), "SetItemTitle");
        Require(SteamUGC.SetItemDescription(handle, item.Description), "SetItemDescription");

        SteamAPICall_t apiCall = SteamUGC.SubmitItemUpdate(
            handle,
            "更新：同步简体中文标题与简介。"
        );

        bool finished = false;
        EResult result = EResult.k_EResultNone;
        bool ioFailure = false;
        bool legalAgreementRequired = false;
        using var callResult = CallResult<SubmitItemUpdateResult_t>.Create((data, failed) =>
        {
            result = data.m_eResult;
            ioFailure = failed;
            legalAgreementRequired = data.m_bUserNeedsToAcceptWorkshopLegalAgreement;
            finished = true;
        });
        callResult.Set(apiCall);

        var deadline = DateTime.UtcNow.AddMinutes(2);
        while (!finished && DateTime.UtcNow < deadline)
        {
            SteamAPI.RunCallbacks();
            Thread.Sleep(100);
        }

        if (!finished)
            throw new TimeoutException($"Timed out updating {item.PublishedFileId}.");
        if (ioFailure || result != EResult.k_EResultOK)
            throw new InvalidOperationException(
                $"Steam rejected {item.PublishedFileId}: result={result}, ioFailure={ioFailure}."
            );
        if (legalAgreementRequired)
            throw new InvalidOperationException(
                $"Steam requires a Workshop legal agreement for {item.PublishedFileId}."
            );

        VerifyLocalizedMetadata(item, language);
        Console.WriteLine($"OK {item.PublishedFileId} language={language} verified=true");
    }
}
finally
{
    SteamAPI.Shutdown();
}

return 0;

static void Require(bool success, string operation)
{
    if (!success)
        throw new InvalidOperationException($"{operation} returned false.");
}

static WorkshopItem ReadManifest(string path)
{
    string value = File.ReadAllText(path);
    ulong id = ulong.Parse(Field(value, "publishedfileid"));
    string title = Unescape(Field(value, "title"));
    string description = Unescape(Field(value, "description"));
    string? contentFolder = OptionalField(value, "contentfolder");
    if (contentFolder is not null)
        contentFolder = Unescape(contentFolder);
    return new WorkshopItem(id, title, description, contentFolder);
}

static string Field(string value, string key)
{
    var match = Regex.Match(
        value,
        $"\"{Regex.Escape(key)}\"\\s*\"((?:\\\\.|[^\"])*)\"",
        RegexOptions.Singleline
    );
    if (!match.Success)
        throw new InvalidDataException($"Missing VDF field: {key}");
    return match.Groups[1].Value;
}

static string? OptionalField(string value, string key)
{
    var match = Regex.Match(
        value,
        $"\"{Regex.Escape(key)}\"\\s*\"((?:\\\\.|[^\"])*)\"",
        RegexOptions.Singleline
    );
    return match.Success ? match.Groups[1].Value : null;
}

static string Unescape(string value) =>
    value.Replace("\\\"", "\"").Replace("\\\\", "\\");

static void VerifyLocalizedMetadata(WorkshopItem expected, string language)
{
    var ids = new[] { new PublishedFileId_t(expected.PublishedFileId) };
    UGCQueryHandle_t query = SteamUGC.CreateQueryUGCDetailsRequest(ids, 1);
    Require(SteamUGC.SetLanguage(query, language), "SetLanguage");
    Require(SteamUGC.SetReturnLongDescription(query, true), "SetReturnLongDescription");

    bool finished = false;
    EResult result = EResult.k_EResultNone;
    bool ioFailure = false;
    using var callResult = CallResult<SteamUGCQueryCompleted_t>.Create((data, failed) =>
    {
        result = data.m_eResult;
        ioFailure = failed;
        finished = true;
    });
    callResult.Set(SteamUGC.SendQueryUGCRequest(query));

    var deadline = DateTime.UtcNow.AddSeconds(30);
    while (!finished && DateTime.UtcNow < deadline)
    {
        SteamAPI.RunCallbacks();
        Thread.Sleep(100);
    }

    try
    {
        if (!finished || ioFailure || result != EResult.k_EResultOK)
            throw new InvalidOperationException(
                $"Localized metadata query failed for {expected.PublishedFileId}: " +
                $"finished={finished}, result={result}, ioFailure={ioFailure}."
            );
        if (!SteamUGC.GetQueryUGCResult(query, 0, out SteamUGCDetails_t details))
            throw new InvalidOperationException(
                $"GetQueryUGCResult failed for {expected.PublishedFileId}."
            );
        if (details.m_rgchTitle != expected.Title ||
            details.m_rgchDescription != expected.Description)
        {
            throw new InvalidOperationException(
                $"Simplified Chinese metadata mismatch for {expected.PublishedFileId}: " +
                $"titleMatch={details.m_rgchTitle == expected.Title}, " +
                $"descriptionMatch={details.m_rgchDescription == expected.Description}."
            );
        }
    }
    finally
    {
        SteamUGC.ReleaseQueryUGCRequest(query);
    }
}

sealed record WorkshopItem(
    ulong PublishedFileId,
    string Title,
    string Description,
    string? ContentFolder
);
