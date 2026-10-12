@echo off
REM TEST SET - ablations of the primary system qwen3:8b (analysis plan v1.0). About 7-9 hours: run overnight.
REM Same rules as run_test_core.bat. Run it after the core script has finished.

python -m mrscreen.freeze annotation_sheet_v1.3.xlsx --verify || goto :stop
python -m mrscreen.lock || goto :stop

python -m mrscreen.run --backend ollama --model qwen3:8b --think off --prompt decomposed --items test5 --set test --frozen --energy --budget 900
python -m mrscreen.run --backend ollama --model qwen3:8b --think off --prompt decomposed --items test5 --set test --frozen --energy --budget 3600
python -m mrscreen.run --backend ollama --model qwen3:8b --think off --prompt decomposed --items test5 --set test --frozen --energy --k 5
python -m mrscreen.run --backend ollama --model qwen3:8b --think on --prompt decomposed --items test5 --set test --frozen --energy --max-new 4096

echo.
echo Done. Zip the new "_test" folders in "runs" and send them. Do not open the predictions.
goto :end
:stop
echo.
echo STOPPED: the gold or the frozen code does not match. Nothing was run. Send me this window.
:end
pause
