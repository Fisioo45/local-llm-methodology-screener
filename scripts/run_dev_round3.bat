@echo off
REM Dev round 3 (2026-10): prompts p2.2 / p1.1 aligned with codebook v1.3, 5 test items, 40 pilot+dev papers.
REM Run from the screener folder with the venv active and Ollama running. About 2.5-3 hours in total.
REM An interrupted run resumes when you start this file again.

python -m mrscreen.run --backend rules --set dev --items test5
python -m mrscreen.run --backend ollama --model qwen3:8b --think off --prompt decomposed --items test5 --set dev --energy
python -m mrscreen.run --backend ollama --model llama3.1:8b --prompt decomposed --items test5 --set dev --energy
python -m mrscreen.run --backend ollama --model qwen3.5:9b --think off --prompt decomposed --items test5 --set dev --energy
python -m mrscreen.run --backend ollama --model gemma3:4b --prompt decomposed --items test5 --set dev --energy
python -m mrscreen.run --backend ollama --model qwen3:8b --think off --items test5 --set dev --energy

echo.
echo Done. Zip the "runs" folder and send it.
pause
