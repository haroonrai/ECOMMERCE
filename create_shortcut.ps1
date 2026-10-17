$wscript = New-Object -ComObject WScript.Shell
$desktopPath = [Environment]::GetFolderPath([Environment+SpecialFolder]::Desktop)
$shortcutPath = Join-Path $desktopPath "AURA Healthcare Store.lnk"
$shortcut = $wscript.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "c:\Users\delta\OneDrive\Ecommerce\Launch_Storefront.bat"
$shortcut.WorkingDirectory = "c:\Users\delta\OneDrive\Ecommerce"
$shortcut.Description = "Open AURA Healthcare & Derma Labs Storefront"
$shortcut.Save()
Write-Host "Desktop shortcut created at: $shortcutPath"
