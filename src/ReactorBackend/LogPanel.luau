--!strict
-- The facility event log: the first reader Engine:Log has ever had.
--
-- Engine:Log writes engine.events and, before this module, nothing anywhere read
-- it. The only other mention of the list in the whole DataModel is MCP_FlowCollector
-- reading its OWN private Engine.new(...), which is a different object entirely.
-- Write-only state with prose standing in for a reader is the same defect class as
-- Phase 54's `judged`; this module is the reader.
--
-- WHERE IT DRAWS, established from the original's own captures rather than assumed.
-- The arithmetic is in PROGRESS.md Phase 65.
--   * The panel is MainMonitorFrame -- the face RoomShell shows in Starting and
--     Running. Its TitleFrame reads SYSTEM LOGS, and its LogsFrame is a 340x365
--     area with a vertical UIListLayout (Padding 0,20) holding no rows at all.
--   * TemplateLogFrame1/2/3 are Visible = false templates at the origin, 340x60,
--     identical except for their TextLabel colour: 0.667,1,1 cyan, 1,0.667,0
--     orange, 1,0.306,0.306 red. Three templates differing only in colour are a
--     colour key -- one per severity -- so a row is a CLONE of the template for
--     its kind and never a write into the template itself.
--   * Writing into the templates, which is what this module did first, draws
--     NOTHING AT ALL: all three are Visible = false. The stale 'E INITIATED' the
--     place carries lives in TemplateLogFrame3 and is left exactly where the art
--     has it, so this module writes to no template and changes no art.
--
-- HOW MANY ROWS. The original's list grows well past what fits -- 26 rows at once
-- during a duplicate-message flood in Data/flow/original_260926-230049, the same
-- flood that finally evicted that stale row -- and the SurfaceGui clips the
-- overflow at four rows. The remake therefore keeps the newest four and evicts the
-- oldest: the same picture, without growing a list nobody can see. The number is a
-- consequence of the art's own geometry (365 / (60 + 20)), not a tunable, which is
-- why it is here and not in Config. Change the art and this changes with it.
--
-- CONTROL is deliberately absent from SHOWN. Engine:Command echoes every accepted
-- command through Log under that kind, and the original's panel does not carry a
-- line per click: across six captures its dumps hold game messages only, never a
-- line per click. Filtering on the kind is the whole reason kind is stored beside
-- the message instead of being read back out of the markup.

local LogPanel = {}

local MONITOR = 'LogControlRoomMonitor'
local MAIN_FRAME = 'MainMonitorFrame'
local LIST_FRAME = 'LogsFrame'

local SHOWN = {ALERT = true, WARN = true, ERROR = true, INFO = true}

-- Which template draws which kind, by the colour the art already gives it. ALERT
-- and ERROR share the red one: both are failures and the panel has three colours,
-- not four.
local TEMPLATE_BY_KIND = {
    INFO  = 'TemplateLogFrame1',
    WARN  = 'TemplateLogFrame2',
    ALERT = 'TemplateLogFrame3',
    ERROR = 'TemplateLogFrame3',
}

local ROWS = 4

type Row = {instance: Frame, kind: string, text: string}

-- The rows this module last drew. It is UI bookkeeping, not game state: the
-- engine owns what was said and this only remembers what it put on the glass, so
-- a re-run can tell 'nothing changed' from 'the list moved' without walking the
-- tree. Entries are re-checked for parentage before being trusted, because a
-- reference that is no longer in the panel means a rebuild, not a no-op.
local rows: {Row} = {}

-- Resolved per call rather than cached. A run without the panel has to degrade to
-- 'no panel', not to an error on every tick, and a monitor built without the log
-- face must not take the whole backend down with it.
local function resolve()
    local monitors = workspace:FindFirstChild('Monitors')
    local monitor = monitors and monitors:FindFirstChild(MONITOR)
    local screen = monitor and monitor:FindFirstChild('Screen')
    local ui = screen and screen:FindFirstChild('MonitorUI')
    local main = ui and ui:FindFirstChild(MAIN_FRAME)
    if not main then return nil end
    local list = main:FindFirstChild(LIST_FRAME)
    if not (list and list:IsA('Frame')) then return nil end
    local templates = {}
    for kind, name in pairs(TEMPLATE_BY_KIND) do
        local template = main:FindFirstChild(name)
        local label = template and template:FindFirstChild('TextLabel')
        if not (template and template:IsA('Frame')) then return nil end
        if not (label and label:IsA('TextLabel')) then return nil end
        templates[kind] = template :: Frame
    end
    return list :: Frame, templates
end

function LogPanel.Refresh(engine)
    local list, templates = resolve()
    if not list then return end

    -- Newest last, walked backwards so the four that show are the newest four
    -- SHOWN, not the newest four recorded: a control echo must not push a message
    -- off the panel, and neither must a message kind the panel does not draw.
    local events = engine.events
    local wanted = {}
    for index = #events, 1, -1 do
        local event = events[index]
        if SHOWN[event.kind] then
            table.insert(wanted, 1, {kind = event.kind, text = event.message})
            if #wanted == ROWS then break end
        end
    end

    -- Guarded because this runs on the main loop: rebuilding four Frames every
    -- tick for a list that has not moved would be pure churn, and the panel is the
    -- one thing here that is visible while it churns.
    local same = #rows == #wanted
    if same then
        for index, item in ipairs(wanted) do
            local row = rows[index]
            if row.kind ~= item.kind or row.text ~= item.text or row.instance.Parent ~= list then
                same = false
                break
            end
        end
    end
    if same then return end

    for _, row in ipairs(rows) do
        if row.instance.Parent then row.instance:Destroy() end
    end
    rows = {}
    for position, item in ipairs(wanted) do
        local clone = templates[item.kind]:Clone()
        -- The templates are authored hidden, and a clone of a hidden frame is
        -- hidden too: this line is the difference between a working panel and a
        -- blank one, and it is why a row cannot simply be the template.
        clone.Visible = true
        -- Explicit order rather than insertion order. UIListLayout sorts by
        -- LayoutOrder first, the copies all arrive carrying the template's own 0,
        -- and ties are then broken by something this module does not control.
        clone.LayoutOrder = position
        local label = clone:FindFirstChild('TextLabel')
        if label and label:IsA('TextLabel') then
            label.Text = item.text
        end
        clone.Parent = list
        table.insert(rows, {instance = clone, kind = item.kind, text = item.text})
    end
end

return LogPanel
