# Records demo.py running in its own classic console window -> demo\demo.mp4
# Run from PowerShell:  powershell -ExecutionPolicy Bypass -File record_demo.ps1
$proj = $PSScriptRoot
$ff = Get-ChildItem "$proj\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-*.exe" | Select-Object -First 1 -ExpandProperty FullName
$out = "$proj\demo"
New-Item -ItemType Directory -Force $out | Out-Null
Remove-Item "$proj\summaries", "$out\demo.mkv", "$out\demo.mp4" -Recurse -Force -ErrorAction SilentlyContinue
$title = "LLMDemo"

# conhost.exe forces a classic console window (Windows Terminal would hide the title from ffmpeg)
$inner = "title $title & mode con: cols=110 lines=38 & color 0A & cd /d `"$proj`" & .venv\Scripts\python.exe -u demo.py & echo. & echo [demo finished] & timeout /t 6 >nul"
$demo = Start-Process conhost.exe -ArgumentList "cmd.exe /c $inner" -PassThru
Start-Sleep -Seconds 3

$ffArgs = @("-y","-f","gdigrab","-framerate","10","-i","title=$title","-vf","pad=ceil(iw/2)*2:ceil(ih/2)*2","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p","$out\demo.mkv")
$rec = Start-Process $ff -ArgumentList $ffArgs -PassThru -WindowStyle Hidden -RedirectStandardError "$out\ffmpeg.log"
Start-Sleep -Seconds 3
if ($rec.HasExited) {
    Write-Host "ffmpeg could not capture the window. Log:" -ForegroundColor Red
    Get-Content "$out\ffmpeg.log" -Tail 6
    exit 1
}
Write-Host "Recording... (do not minimise the green window)"
$demo.WaitForExit(500000) | Out-Null
Start-Sleep -Seconds 1
if (-not $rec.HasExited) { Stop-Process -Id $rec.Id -Force }
Start-Sleep -Seconds 1
& $ff -y -i "$out\demo.mkv" -c copy "$out\demo.mp4" 2>$null
Get-Item "$out\demo.mp4" | Select-Object Name, Length
