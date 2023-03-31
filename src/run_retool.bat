@echo off
setlocal enableextensions
pushd %4
%1 -h %2 -x %3 -skipUnknowns -noExtractDir
popd