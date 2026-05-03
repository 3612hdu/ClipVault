@echo off
echo ============================================
echo ClipVault QA Suite
echo ============================================
echo.
echo [1/2] Running pytest (unit + integration)...
python -m pytest tests/ -v --tb=short
echo.
echo [2/2] Running E2E user simulation...
python tests/test_clipboard_integration.py
echo.
echo QA Complete.
pause
