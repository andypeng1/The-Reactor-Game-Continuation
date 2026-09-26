# Zero-install capability probe: can I (a) read the screen to a file, and
# (b) move the mouse?  The mouse test is a round trip and restores the original
# position, so worst case the cursor twitches 40 px and comes back.
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# --- (a) screenshot to a file ---
$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
$out = Join-Path $PSScriptRoot 'probe_shot.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
$fi = Get-Item $out
Write-Output ("A screenshot : {0} x {1} px -> {2} bytes ({3} KB)" -f $b.Width, $b.Height, $fi.Length, [int]($fi.Length / 1KB))

# --- (b) mouse read / move / read / restore ---
Add-Type -Namespace W -Name U -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool GetCursorPos(out System.Drawing.Point p);
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
'@
$p0 = New-Object System.Drawing.Point
[void][W.U]::GetCursorPos([ref]$p0)
Write-Output ("B mouse read : before  ({0}, {1})" -f $p0.X, $p0.Y)
[void][W.U]::SetCursorPos($p0.X + 40, $p0.Y)
Start-Sleep -Milliseconds 60
$p1 = New-Object System.Drawing.Point
[void][W.U]::GetCursorPos([ref]$p1)
Write-Output ("C mouse move : after   ({0}, {1})   -> moved {2} px" -f $p1.X, $p1.Y, ($p1.X - $p0.X))
[void][W.U]::SetCursorPos($p0.X, $p0.Y)
$p2 = New-Object System.Drawing.Point
[void][W.U]::GetCursorPos([ref]$p2)
Write-Output ("D restored   : back to ({0}, {1})" -f $p2.X, $p2.Y)
