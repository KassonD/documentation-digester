@echo off
echo =========================================
echo Digesting...
echo =========================================

cd documentation-digester && uv run python -m documentation_digester.digester.pipeline

echo =========================================
echo Digestion Complete!
echo =========================================

pause