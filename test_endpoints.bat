@echo off
setlocal enabledelayedexpansion

REM konfigurasi
set API_BASE=http://127.0.0.1:8000
set USERNAME=sam_test
set PASSWORD=Secret123

echo ========== 1) Try register new user ==========
curl -s -X POST "%API_BASE%/auth/register" -H "Content-Type: application/json" -d "{\"username\":\"%USERNAME%\",\"password\":\"%PASSWORD%\"}" > tmp_register.json
type tmp_register.json
echo.

echo ========== 2) Login to get token ==========
curl -s -X POST "%API_BASE%/auth/login" -H "Content-Type: application/x-www-form-urlencoded" -d "username=%USERNAME%&password=%PASSWORD%" > tmp_login.json
type tmp_login.json
echo.

REM Extract access_token using python (robust parsing)
for /f "delims=" %%A in ('python -c "import json,sys; print(json.load(open('tmp_login.json')).get('access_token',''))"') do set TOKEN=%%A

if "%TOKEN%"=="" (
    echo ERROR: token not found. Aborting further requests.
    echo Check tmp_login.json for details.
    goto :cleanup
)

echo Token extracted: %TOKEN:~0,40%...
echo.

echo ========== 3) Run RAG query (authenticated) ==========
curl -s -X POST "%API_BASE%/rag/rag/query" -H "Authorization: Bearer %TOKEN%" -H "Content-Type: application/json" -d "{\"query\":\"Jelaskan AutoMIND secara singkat\",\"top_k\":3}" > tmp_query.json
type tmp_query.json
echo.

echo ========== 4) Fetch history (authenticated) ==========
curl -s -H "Authorization: Bearer %TOKEN%" "%API_BASE%/rag/rag/history?limit=20&offset=0" > tmp_history.json
type tmp_history.json
echo.

:cleanup
del /Q tmp_register.json 2>nul
del /Q tmp_login.json 2>nul
del /Q tmp_query.json 2>nul
del /Q tmp_history.json 2>nul

echo Done.
endlocal
