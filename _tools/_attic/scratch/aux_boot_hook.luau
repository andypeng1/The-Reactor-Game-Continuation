-- The provenance of Data/auxcollection/startup/ScreenChanges.txt.
--
-- Handed over by the operator on 2026-10-01, verbatim, as the script that
-- produced that capture.  It answers the one question the capture itself
-- cannot: WHERE t=0 IS.  The file's own Time:[...] column starts at 19:21:59
-- and the writer frames a t=0 only relative to its own first record, so on the
-- bytes alone "t=0" could be any moment -- and I had guessed wrong, writing in
-- PROGRESS.md Phase 66.5 that the capture had begun mid-boot.
--
-- It begins on a ClickDetector.MouseClick:
--
--     workspace.Consoles.MainReactorConsole.MonitorBootButton.ClickPart
--              .ClickDetector.MouseClick
--
-- i.e. on the MONITOR BOOT BUTTON press itself, which is the original's own
-- Cold -> Booting transition.  Two consequences, both now in the record:
--   1. The capture is a STANDARD startup, not a quick boot.
--   2. The 0..13 s BootFrame window it shows is a measurement of the boot
--      length, which is what Config.Shift.BootSeconds is.
--
-- The three names below (wn, StartRecording, WatchTimeLabel) are the operator's
-- own harness and are NOT defined here -- this file is the hook, not the
-- recorder.  Kept verbatim; do not "fix" it into something runnable, because
-- what it is evidence FOR is the connect target and the closure body, not the
-- harness around them.

wn(function()
    print("等待按钮点击...")
    local ClickDetector = workspace:WaitForChild("Consoles", 60)
        and workspace.Consoles:WaitForChild("MainReactorConsole", 60)
        and workspace.Consoles.MainReactorConsole:WaitForChild("MonitorBootButton", 60)
        and workspace.Consoles.MainReactorConsole.MonitorBootButton:WaitForChild("ClickPart", 60)
        and workspace.Consoles.MainReactorConsole.MonitorBootButton.ClickPart:WaitForChild("ClickDetector", 60)

    if not ClickDetector then
        warn("Fatal Error: 无法找到 ClickDetector")
        return
    end

    ClickDetector.MouseClick:Connect(function()
        print("按钮被点击，启动记录")
        StartRecording()
        WatchTimeLabel()
    end)
end)
