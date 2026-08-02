param(
    [Parameter(Mandatory = $true)]
    [string[]]$Path
)

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$settings = [System.Xml.XmlWriterSettings]::new()
$settings.Encoding = $utf8NoBom
$settings.Indent = $true
$settings.IndentChars = "  "
$settings.NewLineChars = "`r`n"
$settings.NewLineHandling = [System.Xml.NewLineHandling]::Replace

$changedFiles = 0
$wrappedOperations = 0

foreach ($filePath in $Path) {
    $resolved = (Resolve-Path -LiteralPath $filePath).Path
    $document = [System.Xml.XmlDocument]::new()
    $document.PreserveWhitespace = $false
    $document.Load($resolved)

    $operations = @($document.SelectNodes('/Patch/Operation[@Class="PatchOperationReplace"]'))
    if ($operations.Count -eq 0) {
        continue
    }

    foreach ($operation in $operations) {
        $sourceXPath = $operation.SelectSingleNode('xpath')
        if ($null -eq $sourceXPath) {
            continue
        }

        $conditional = $document.CreateElement('Operation')
        $conditional.SetAttribute('Class', 'PatchOperationConditional')

        $success = $document.CreateElement('success')
        $success.InnerText = 'Always'
        [void]$conditional.AppendChild($success)
        [void]$conditional.AppendChild($sourceXPath.CloneNode($true))

        $match = $document.CreateElement('match')
        $match.SetAttribute('Class', 'PatchOperationReplace')
        foreach ($child in @($operation.ChildNodes)) {
            [void]$match.AppendChild($child.CloneNode($true))
        }
        [void]$conditional.AppendChild($match)

        [void]$operation.ParentNode.ReplaceChild($conditional, $operation)
        $wrappedOperations++
    }

    $writer = [System.Xml.XmlWriter]::Create($resolved, $settings)
    try {
        $document.Save($writer)
    }
    finally {
        $writer.Dispose()
    }
    $changedFiles++
}

Write-Output "changed_files=$changedFiles wrapped_operations=$wrappedOperations"
