@echo off
rem Wrapper so the dev-server runner finds Node even when its PATH is stale.
set "PATH=C:\Program Files\nodejs;%PATH%"
call "C:\Program Files\nodejs\npm.cmd" --prefix "%~dp0..\frontend" run dev
