@echo off
REM Start the EasyMart Support Agent demo UI

cls
echo.
echo ========================================
echo EasyMart Support Agent - Demo UI
echo ========================================
echo.
echo Starting Streamlit app...
echo.
echo The app will open in your browser at:
echo    http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

streamlit run app.py
