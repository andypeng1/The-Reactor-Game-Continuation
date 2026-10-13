--!strict
-- The half of the end-of-shift flow the original did with a teleport.
--
-- EndShiftHandler hides the vitals, the affliction list, the settings button and
-- the backpack, shows the report, and -- once a player holds the acknowledge
-- button -- swaps the report for the intermission. In the original the player
-- was then teleported: a respawn re-clones StarterGui, and that is what put all
-- of it back. This place has no teleport and no lobby (no TeleportService call
-- exists anywhere in it), so without this script a shift can be restarted while
-- the screen stays on top of the world forever -- which is the same dead end one
-- step further along, and the operator's own complaint.
--
-- The trigger is the reply EndShiftBridge sends on an ACCEPTED transition, on
-- the same MiscEvent.OnClientEvent the legacy screen already reads. A refused
-- request therefore closes nothing, because nothing changed.
--
-- The authored visibility and volumes are CAPTURED at boot rather than listed
-- here, so this cannot drift from what the UI was actually authored with
-- (CLAUDE.md 0.24: the baseline for restoring a world is read off that world,
-- never remembered).

local Players = game:GetService('Players')
local SoundService = game:GetService('SoundService')
local StarterGui = game:GetService('StarterGui')

local playerGui = Players.LocalPlayer:WaitForChild('PlayerGui')
local screenGui = playerGui:WaitForChild('ScreenGui')

-- {instance, property, value}: everything the report screen changes about the
-- rest of the interface, read before anything has had a chance to change it.
local captured = {}
local function remember(instance, property)
    if not instance then return end
    local ok, value = pcall(function() return instance[property] end)
    if not ok then return end
    table.insert(captured, {instance = instance, property = property, value = value})
end

local endGameFrame = screenGui:WaitForChild('EndGameFrame1')
local intermission = screenGui:FindFirstChild('IntermissionFrame')
for _, name in ipairs({'MESUI', 'VitalsFrame', 'AfflictionFrame', 'SettingsButton', 'SettingsShadow'}) do
    remember(screenGui:FindFirstChild(name), 'Visible')
end
remember(endGameFrame:FindFirstChild('TextButton'), 'Visible')
remember(screenGui:FindFirstChild('SequenceStatic'), 'ImageTransparency')
-- Every sound the report silences except the music it keeps. Captured as a set
-- rather than as a hardcoded list for the same reason as the frames above.
for _, sound in ipairs(SoundService:GetChildren()) do
    if sound.Name ~= 'MusicSounds' then remember(sound, 'Volume') end
end
local staticSound = workspace:FindFirstChild('Sounds')
staticSound = staticSound and staticSound:FindFirstChild('Effects')
staticSound = staticSound and staticSound:FindFirstChild('External')
staticSound = staticSound and staticSound:FindFirstChild('StaticSound')
remember(staticSound, 'PlaybackSpeed')

local function restoreAuthored()
    for _, entry in ipairs(captured) do
        pcall(function() entry.instance[entry.property] = entry.value end)
    end
end

-- A finished transition: the screen has done its job, so it comes down and the
-- interface it took over comes back.
local function closeReport()
    restoreAuthored()
    endGameFrame.Visible = false
    if intermission then intermission.Visible = false end
    -- Re-enabled here because it is turned off by the report and only ever
    -- turned back on by a respawn -- which this place never causes.
    pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, true) end)
end

-- A refused one: the player is left holding a report that did not take effect.
-- Hand the report back rather than the intermission, so the other two buttons
-- are still in front of them.
local function backToReport()
    endGameFrame.Visible = true
    if intermission then intermission.Visible = false end
end

local miscEvent = game:GetService('ReplicatedStorage'):WaitForChild('MiscEvent')
miscEvent.OnClientEvent:Connect(function(reply)
    if type(reply) ~= 'table' then return end
    if reply[3] == 'Accepted' and (reply[1] == 'Next' or reply[1] == 'Reset') then
        closeReport()
    elseif reply[3] == 'Refused' then
        backToReport()
    end
end)
