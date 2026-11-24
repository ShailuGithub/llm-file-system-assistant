$proj = "D:\SHAILESH\llm-file-assistant"
$ff = "$proj\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
$out = "$proj\demo"
New-Item -ItemType Directory -Force $out | Out-Null
Remove-Item "$proj\summaries" -Recurse -Force -ErrorAction SilentlyContinue
$title = "LLM File Assistant Demo"

# demo window: fixed size, titled so ffmpeg can capture only this window
$cmd = "title $title & mode con: cols=110 lines=38 & color 0A & cd /d $proj & .venv\Scripts\python.exe -u demo.py & echo. & echo [demo finished] & timeout /t 6 >nul"
$demo = Start-Process cmd.exe -ArgumentList "/c", $cmd -PassThru
Start-Sleep -Seconds 2

$ffArgs = @("-y","-f","gdigrab","-framerate","10","-i","title=$title","-vf","pad=ceil(iw/2)*2:ceil(ih/2)*2","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p","$out\demo.mkv")
$rec = Start-Process $ff -ArgumentList $ffArgs -PassThru -WindowStyle Hidden
$demo.WaitForExit(400000) | Out-Null
Start-Sleep -Seconds 1
Stop-Process -Id $rec.Id -Force
Start-Sleep -Seconds 1
& $ff -y -i "$out\demo.mkv" -c copy "$out\demo.mp4" 2>$null
Get-Item "$out\demo.*" | Select Name, Length
