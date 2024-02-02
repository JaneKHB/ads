@ECHO OFF

IF EXIST crasapp (
     echo Delete old crasapp folder.
     rmdir crasapp /s /q
)

mkdir crasapp

ECHO Copy all files to run as a cras-server.

copy ..\..\main.py .\crasapp

SET folders=common config controller dao flaskapp resource service dockerlib
(FOR %%a IN (%folders%) DO (
    xcopy ..\..\%%a .\crasapp\%%a\ /E /H
))

mkdir crasapp\pyrunner
mkdir crasapp\pyrunner\src
copy ..\..\pyrunner\src\steprunnerhost.py .\crasapp\pyrunner\src

ECHO Create a achieve file.
tar cvf cras.tar crasapp

ECHO Clean up all temporaries.
rmdir crasapp /s /q

ECHO Success