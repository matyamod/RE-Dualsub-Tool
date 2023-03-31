@echo off
setlocal enableextensions
pushd %~dp0
echo Original file list: %1

findstr \.msg\. %1 > custom.list
findstr \.fslt\. %1 >> custom.list
findstr \.gui\. %1 >> custom.list
popd