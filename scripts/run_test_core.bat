@echo off
REM TEST SET - core systems (analysis plan v1.0, section 2). About 3.5-4 hours.
REM Run from the screener folder in the Anaconda Prompt with "conda activate kgc", Ollama running.
REM Do NOT run "ollama pull" before or during these runs (model digests are locked).
REM An interrupted run resumes when you start this file again.

python -m mrscreen.freeze annotation_sheet_v1.3.xlsx --verify || goto :stop
python -m mrscreen.lock || goto :stop

python -m mrscreen.run --backend rules --set test --frozen --items test5
python -m mrscreen.run --backend ollama --model qwen3:8b --think off --prompt decomposed --items test5 --set test --frozen --energy
python -m mrscreen.run --backend ollama --model qwen3.5:9b --think off --prompt decomposed --items test5 --set test --frozen --energy
python -m mrscreen.run --backend ollama --model llama3.1:8b --prompt decomposed --items test5 --set test --frozen --energy
python -m mrscreen.run --backend ollama --model gemma3:4b --prompt decomposed --items test5 --set test --frozen --energy
python -m mrscreen.run --backend ollama --model qwen3:8b --think off --items test5 --set test --frozen --energy

echo.
echo Done. Zip the new "_test" folders in "runs" and send them. Do not open the predictions.
goto :end
:stop
echo.
echo STOPPED: the gold or the frozen code does not match. Nothing was run. Send me this window.
:end
pause
