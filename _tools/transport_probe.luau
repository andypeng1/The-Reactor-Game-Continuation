-- transport_probe.luau -- which HTTP transports can THIS executor actually use?
--
-- WHY IT EXISTS.  The watcher delivered zero bytes in the 12:32 run while the
-- recorder delivered a complete file through the same sink in the same session,
-- and the one structural difference between them is the transport: the recorder
-- tries the executor's own request functions first and falls back to
-- HttpService:PostAsync last, while the watcher calls HttpService:PostAsync and
-- nothing else.  The recorder's own comment says why that ordering is the way it
-- is -- "HttpService:PostAsync is not an executor function and a plain client is
-- not allowed to call it -- it raises at once" -- so the two files have been
-- assuming opposite things about the same call, and the silent watcher is what
-- that looks like from the reading end.
--
-- This is a PROBE and not a diagnostic: it costs one injection and no shift, and
-- it answers the question by trying every candidate and naming the ones that
-- worked.  Run it before the lever, not during a run.
--
-- HOW TO READ IT.  Whatever comes back, the answer is a FILE, because the whole
-- point is that the file's existence is the measurement.  One file per candidate
-- is POSTed through that candidate; a candidate that cannot post cannot write its
-- own file, so:
--     Data/probe/<stamp>/syn.txt        present  => syn.request WORKS
--     Data/probe/<stamp>/http.txt       present  => HttpService:PostAsync WORKS
--     Data/probe/<stamp>/summary.txt    present  => written by the first candidate
--                                       that worked, and it names all of them
-- A missing http.txt next to a present syn.txt is the whole finding: the watcher
-- was posting through the one transport this executor does not have.
--
-- It also prints, unlike the watcher, and deliberately.  A probe whose output
-- goes only to a sink you cannot reach has no way to tell "the transport is
-- missing" from "the script never ran" -- which is the exact ambiguity that made
-- this file necessary.  The console is the second channel, and for a one-shot
-- probe it is the right one.
--
-- READ-ONLY: it touches nothing in the game, and the only global it writes is
-- its own name, so a re-run replaces it instead of stacking up.

local NL = string.char(10)

-- The recorder's sink, same port and same directory (receive.py --dir Data/).
local SINK = 'http://127.0.0.1:8765/'

-- One directory per injection, so a re-run cannot be confused with the run before
-- it -- the whole value here is "did THIS injection get through".
local STAMP = (function()
	local ok, d = pcall(os.date, '%y%m%d-%H%M%S')
	return (ok and type(d) == 'string') and d or tostring(os.time())
end)()
local PREFIX = 'probe/' .. STAMP .. '/'

-- The candidate order is the recorder's, and it is not alphabetical: the
-- executor's own functions first (they are the ones that work from a client) and
-- HttpService last (it is the one that raises there).  Each entry is a name and a
-- thunk returning the callable, because a table holding nils would stop ipairs at
-- the first missing one and silently skip the rest -- the bug that comment in the
-- recorder warns about, and the reason every candidate is a function here too.
local CANDIDATES = {
	{ 'syn', 'post', function() return syn and syn.request end },
	{ 'http_request', 'post', function() return http_request end },
	{ 'request', 'post', function() return request end },
	{ 'http', 'post', function() return http and http.request end },
	{ 'fluxus', 'post', function() return fluxus and fluxus.request end },
	{ 'krnl', 'post', function() return krnl and krnl.request end },
	{ 'getgenv', 'post', function() return getgenv and getgenv().request end },
	-- A GET, and marked as one.  This is how the scripts themselves are fetched
	-- (`loadstring(game:HttpGet(...))`), so it is the transport most likely to be
	-- present -- but the sink DISCARDS a GET body today (receive.py answers
	-- "receiver up" and writes nothing), so `reachable` here means the channel
	-- exists and not that a byte could be delivered through it.  Kept in the list
	-- because the answer changes what the fallback has to be: if this is the only
	-- one that works, the sink needs teaching to take data on a GET before the
	-- watcher can use it.
	{ 'httpget', 'get', function() return game and game.HttpGet end },
	-- Last, and the one under suspicion.  Positional in the real API, so it is the
	-- one candidate whose wrapper has to do work -- see the calling shape below.
	{ 'httpservice', 'post', function()
		if game == nil then return nil end
		local ok, hs = pcall(function() return game:GetService('HttpService') end)
		if not ok or hs == nil then return nil end
		return function(req)
			local posted, err = pcall(function()
				return hs:PostAsync(req.Url, req.Body)
			end)
			if posted then return { StatusCode = 200 } end
			-- The raise text is kept, unlike the recorder's wrapper which throws it
			-- away for a bare StatusCode 0.  The recorder can afford to forget: it
			-- only needs to know whether to fall through.  A probe that reports
			-- "does not work" without the reason has answered half the question,
			-- and this candidate is the whole reason the file exists.
			return { StatusCode = 0, Error = tostring(err) }
		end
	end },
}

-- ONE POST ATTEMPT, IN THE SHIPPED CALLING SHAPE.
--
-- This is a request TABLE and not (url, body), and getting it wrong is silent in
-- the worst way.  `syn.request` and its siblings take a table; handed a string
-- they raise, or -- in a stub -- return nothing useful, and the probe would report
-- a working transport as broken.  The shape here is the recorder's, verbatim
-- (postSegment, `{Url = ..., Method = 'POST', Body = ..., Headers = ...}`), so the
-- probe measures the call the shipped scripts actually make and not a call that
-- merely looks equivalent.
--
-- Returns ok, detail -- where `detail` is the failure reason when it failed, so
-- the table the probe prints names the cause and not just the verdict.
local function attempt(send, url, body)
	local ok, res = pcall(send, {
		Url = url, Method = 'POST', Body = body,
		Headers = { ['Content-Type'] = 'text/plain' },
	})
	if not ok then return false, 'raised: ' .. tostring(res) end
	if type(res) ~= 'table' then return false, 'no result table' end
	-- The recorder reads StatusCode or Status; `status`/`code` are here because an
	-- executor that spells it differently is still a working transport, and reading
	-- it as "no status code" would retire the wrong candidate.
	local code = tonumber(res.StatusCode) or tonumber(res.Status) or
		tonumber(res.statusCode) or tonumber(res.status) or tonumber(res.code)
	if code == nil then return false, 'no status code in the result' end
	if code < 200 or code > 299 then
		-- The transport's own words, when it has any.  `status 0` alone is what a
		-- wrapper hands back after a raise, and the raise is the interesting part.
		local extra = res.Error or res.error or res.Body
		return false, 'status ' .. tostring(code) ..
			(extra and (' (' .. tostring(extra) .. ')') or '')
	end
	return true, 'status ' .. tostring(code)
end

-- The body of each candidate's own file.  It names the transport, so the file is
-- self-describing even when it is moved out of its directory.
local function report(name, kind, present, works, detail)
	return table.concat({
		'# transport_probe: ' .. name .. ' delivered this file, so it WORKS',
		'name=' .. name,
		'kind=' .. kind,
		'present=' .. tostring(present),
		'works=' .. tostring(works),
		'detail=' .. tostring(detail),
		'place=' .. tostring(game and game.PlaceId or '?'),
		'executor=' .. tostring((function()
			local ok2, id = pcall(function() return identifyexecutor and identifyexecutor() end)
			return (ok2 and id) or '?'
		end)()),
	}, NL) .. NL
end

local summary = {}
local winner = nil

for _, cand in ipairs(CANDIDATES) do
	local name, kind, get = cand[1], cand[2], cand[3]
	local present, send = false, nil
	local got, f = pcall(get)
	if got and type(f) == 'function' then present = true; send = f end

	local works, detail
	if not present then
		works, detail = false, 'not present in this executor'
	elseif kind == 'get' then
		-- A GET is read differently and says less: the reading is "a body came
		-- back", not "a file appeared".  The sink answers every GET with
		-- 'receiver up' and writes nothing, so a channel that answers here still
		-- delivers zero bytes until the sink is taught to accept them.
		local called, body = pcall(send, SINK .. PREFIX .. name .. '.txt?reachability=1')
		-- Positional, and that is not an inconsistency with the POST shape below:
		-- `HttpGet` is a Roblox API method, so the url is the argument, whereas the
		-- executor request family takes a table.  The wrapper is per-candidate for
		-- exactly this reason.
		if not called then
			works, detail = false, 'raised: ' .. tostring(body)
		elseif type(body) == 'string' and #body > 0 then
			works, detail = true, 'channel answered, ' .. tostring(#body) ..
				' bytes (a GET writes nothing at the sink)'
		else
			works, detail = false, 'no body came back'
		end
	else
		works, detail = attempt(send, SINK .. PREFIX .. name .. '.txt',
			report(name, kind, present, true, 'posted'))
	end

	summary[#summary + 1] = string.format('%-12s %-4s present=%-5s works=%-5s %s',
		name, kind, tostring(present), tostring(works), detail)
	-- A winner must be able to DELIVER, so a reachable GET is not one.
	if works and winner == nil and kind == 'post' then winner = name end
	print(string.format('[probe] %-12s %-4s present=%s works=%s %s',
		name, kind, tostring(present), tostring(works), detail))
end

-- The summary goes out through the FIRST transport that worked, so the file's
-- existence is itself evidence about that transport rather than about the sink.
-- With none working there is no file and no summary -- and then the console table
-- above is the entire result, which is why it prints.
if winner ~= nil then
	local get = nil
	for _, cand in ipairs(CANDIDATES) do
		if cand[1] == winner then get = cand[3] end
	end
	local ok2, send = pcall(get)
	if ok2 and type(send) == 'function' then
		local body = table.concat({
			'# transport_probe summary -- sent through the first transport that worked',
			'winner=' .. winner,
			'prefix=' .. PREFIX,
			'',
			table.concat(summary, NL),
		}, NL) .. NL
		local ok, detail = attempt(send, SINK .. PREFIX .. 'summary.txt', body)
		print(string.format('[probe] summary via %s: %s %s', winner, tostring(ok), detail))
	end
else
	print('[probe] NO transport worked. The console table above is the whole result.')
end

_G.TRG_TRANSPORT_PROBE = { stamp = STAMP, winner = winner, summary = summary }
return true
