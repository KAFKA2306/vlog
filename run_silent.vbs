CreateObject("WScript.Shell").Run "cmd /c """ & Replace(WScript.ScriptFullName,"run_silent.vbs","run.bat") & """", 0, False
