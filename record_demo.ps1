# Records demo.py running in its own classic console window -> demo\demo.mp4
# Run from PowerShell:  powershell -ExecutionPolicy Bypass -File record_demo.ps1
$proj = $PSScriptRoot
$ff = Get-ChildItem "$proj\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-*.exe" | Select-Object -First 1 -ExpandProperty FullName
$out = "$proj\demo"
New-Item -ItemType Directory -Force $out | Out-Null
Remove-Item "$proj\summaries", "$out\demo.mkv", "$out\demo.mp4" -Recurse -Force -ErrorAction SilentlyContinue
$title = "LLMDemo"

# conhost.exe forces a classic console window (Windows Terminal would hide the title from ffmpeg)
$inner = "title $title & mode con: cols=120 lines=40 & color 0A & cd /d `"$proj`" & .venv\Scripts\python.exe -u demo.py & echo. & echo [demo finished] & timeout /t 6 >nul"
$demo = Start-Process conhost.exe -ArgumentList "cmd.exe /c $inner" -PassThru
Start-Sleep -Seconds 2
Add-Type -Name W -Namespace N -MemberDefinition '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);'
$h = (Get-Process | Where-Object { $_.MainWindowTitle -like "*LLMDemo*" } | Select-Object -First 1).MainWindowHandle
if ($h) { [N.W]::ShowWindow($h,3) | Out-Null }
Start-Sleep -Seconds 1

$ffArgs = @("-y","-f","gdigrab","-framerate","10","-i","desktop","-vf","scale=1920:-2","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p","-movflags","frag_keyframe+empty_moov","$out\demo.mp4")
$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = $ff; $psi.Arguments = ($ffArgs -join " "); $psi.UseShellExecute = $false; $psi.RedirectStandardInput = $true; $psi.RedirectStandardError = $true; $psi.CreateNoWindow = $true
$rec = [Diagnostics.Process]::Start($psi)
$null = $rec.StandardError.ReadToEndAsync()
Start-Sleep -Seconds 3
if ($rec.HasExited) {
    Write-Host "ffmpeg could not capture the window. Log:" -ForegroundColor Red
    $rec.StandardError.ReadToEnd() | Select-Object -Last 6
    exit 1
}
Write-Host "Recording... (do not minimise the green window)"
$demo.WaitForExit(500000) | Out-Null
Start-Sleep -Seconds 1
if (-not $rec.HasExited) { $rec.StandardInput.WriteLine("q"); $rec.StandardInput.Flush(); $rec.WaitForExit(15000) | Out-Null }
if (-not $rec.HasExited) { Stop-Process -Id $rec.Id -Force }
Start-Sleep -Seconds 1
Get-Item "$out\demo.mp4" | Select-Object Name, Length


