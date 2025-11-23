CreateObject("WScript.Shell").Run "cmd /c """ & Replace(WScript.ScriptFullName,"run_silent.vbs","run.cmd") & """", 0, False
