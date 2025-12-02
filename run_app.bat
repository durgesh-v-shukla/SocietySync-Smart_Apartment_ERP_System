@echo off
REM SocietySync ERP - Run Application Script (Batch)

echo =====================================================
echo   🏢 SocietySync ERP - Starting Application
echo =====================================================
echo.
echo Database: postgresql://postgres:***@localhost:5432/societysync
echo Port:     8501
echo.
echo Access the application at:
echo   → http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo =====================================================
echo.

REM Set the database connection URL
set DATABASE_URL=postgresql://postgres:root@localhost:5432/societysync

REM Run Streamlit application
streamlit run app.py --server.port 8501