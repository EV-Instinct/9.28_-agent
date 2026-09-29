@echo off
chcp 65001 >nul
title 正在启动 AI李白·望天门山研学助手...

echo ========================================================
echo        ⛵ AI李白 · 望天门山数字化研学助手 ⛵
echo            小学语文三年级（部编版）专设终端
echo ========================================================
echo.

set PYTHON_CMD=python
if exist "D:\python\python.exe" (
    set PYTHON_CMD=D:\python\python.exe
)

echo [1/2] 正在加载青年李白核心大脑与微软Edge-TTS语音引擎...
echo [2/2] 正在拉起国风水墨大屏交互界面...
echo.
echo 系统即将自动在默认浏览器中打开页面：http://localhost:8501
echo （如未自动弹出，请手动在浏览器访问该地址）
echo.

"%PYTHON_CMD%" -m streamlit run app.py --server.port 8501 --browser.gatherUsageStats false

pause
