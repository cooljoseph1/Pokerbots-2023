@echo off
setlocal enabledelayedexpansion

for /l %%x in (1, 1, 20) do (
    call python run.py python_skeleton_minimax python_skeleton_old
)
