@echo off
REM SocietySync ERP - Run Application Script (Batch)

REM Load DATABASE_URL from .env file if it exists
set "DATABASE_URL="
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if /i "%%A"=="DATABASE_URL" set "DATABASE_URL=%%B"
    )
)

REM If DATABASE_URL is still not set, prompt the user
if "%DATABASE_URL%"=="" (
    echo No .env file found or DATABASE_URL not set.
    echo Please enter your DATABASE_URL:
    echo   Example: postgresql://postgres:yourpassword@localhost:5432/societysync
    set /p DATABASE_URL="DATABASE_URL= "
)

REM Mask the password for display
for /f "tokens=1,2 delims=@" %%A in ("%DATABASE_URL%") do (
    for /f "tokens=1 delims=:" %%C in ("%%A") do (
        set "DB_DISPLAY=%%C://***:***@%%B"
    )
)

echo =====================================================
echo   SocietySync ERP - Starting Application
echo =====================================================
echo.
echo Database: %DB_DISPLAY%
echo Port:     8501
echo.
echo Access the application at:
echo   http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo =====================================================
echo.

REM Run Streamlit application
streamlit run app.py --server.port 8501
