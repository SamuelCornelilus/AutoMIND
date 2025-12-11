@echo off
set BACKUP_DIR=backup_sqlite
if not exist %backup_sqlite% mkdir %backup_sqlite%
set TIMESTAMP=%%-%2/%-%02%_%17%%23%%21%
set TIMESTAMP=%%TIMESTAMP:0=0%%
copy backend\app\db.sqlite %backup_sqlite%\db_%%TIMESTAMP: =0%%.sqlite
echo Backup created: %backup_sqlite%\db_%%TIMESTAMP: =0%%.sqlite
