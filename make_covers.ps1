<#
Copies each source Workshop preview into its Chinese localization package and
adds a consistent, readable Chinese-localization badge.  Source artwork is
preserved; only the lower banner is added.
#>

param(
    [string]$WorkshopRoot = 'D:\SteamLibrary\steamapps\workshop\content\294100',
    [string]$OutputRoot = 'D:\MODS\Rimworld'
)

Add-Type -AssemblyName System.Drawing

$fallbackPreview = @{ '3223844717' = '2394460334' }
$fontFamily = 'Microsoft YaHei'
# Keep the script compatible with Windows PowerShell's legacy ANSI parser.
$zhLabel = ([string][char]0x7B80) + ([string][char]0x4F53) + ([string][char]0x4E2D) + ([string][char]0x6587) + ([string][char]0x6C49) + ([string][char]0x5316)

Get-ChildItem -LiteralPath $OutputRoot -Directory | ForEach-Object {
    $package = $_
    $id = $package.Name.Substring(0, 10)
    $sourceId = if ($fallbackPreview.ContainsKey($id)) { $fallbackPreview[$id] } else { $id }
    $source = Join-Path $WorkshopRoot "$sourceId\About\Preview.png"
    if (-not (Test-Path -LiteralPath $source)) {
        Write-Warning "No preview found for $($package.Name)"
        return
    }

    $image = [System.Drawing.Image]::FromFile($source)
    try {
        $canvas = New-Object System.Drawing.Bitmap($image.Width, $image.Height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
        $graphics = [System.Drawing.Graphics]::FromImage($canvas)
        try {
            $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
            $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
            $graphics.DrawImage($image, 0, 0, $image.Width, $image.Height)

            $text = if ($id -eq '3223844717') { 'EX - ' + $zhLabel } else { $zhLabel }
            $fontSize = [Math]::Max(20, [Math]::Round($image.Width * 0.038))
            $font = New-Object System.Drawing.Font($fontFamily, $fontSize, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
            try {
                $size = $graphics.MeasureString($text, $font)
                $padX = [Math]::Round($image.Width * 0.028)
                $padY = [Math]::Round($image.Height * 0.022)
                $bannerHeight = [Math]::Ceiling($size.Height + 2 * $padY)
                $bannerWidth = [Math]::Ceiling($size.Width + 2 * $padX)
                $x = [Math]::Round($image.Width * 0.025)
                $y = $image.Height - $bannerHeight - [Math]::Round($image.Height * 0.03)
                $rect = New-Object System.Drawing.Rectangle($x, $y, $bannerWidth, $bannerHeight)
                $fill = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(220, 10, 24, 34))
                $border = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(255, 77, 220, 240), [Math]::Max(2, [Math]::Round($image.Width * 0.004)))
                $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
                try {
                    $graphics.FillRectangle($fill, $rect)
                    $graphics.DrawRectangle($border, $rect)
                    $graphics.DrawString($text, $font, $textBrush, $x + $padX, $y + $padY - 2)
                } finally {
                    $fill.Dispose(); $border.Dispose(); $textBrush.Dispose()
                }
            } finally {
                $font.Dispose()
            }
            $destination = Join-Path $package.FullName 'About\Preview.png'
            $canvas.Save($destination, [System.Drawing.Imaging.ImageFormat]::Png)
            Write-Output "Created $destination"
        } finally {
            $graphics.Dispose(); $canvas.Dispose()
        }
    } finally {
        $image.Dispose()
    }
}
