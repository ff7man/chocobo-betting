-- This lua scripts generates chocobo race data
-- The script assumes a save state where you are waiting to press O to load the bet screen
-- manually delete first two races

rank = "c"
slot = 4
-- Converts a big endian hex string name to text 
function decodeName(myin)
    local a = ' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~'
	local res = ''
	local i = 1

	while i <= string.len(myin) do
		local val = string.sub(myin, i, i + 1)
		local dec = tonumber(val, 16)
	  
		if dec >= string.len(a) then
			if dec ~= 255 then
				--print('replacing char: ' .. val .. ' with space')
				dec = 0
			end
		end
		res = res .. string.sub(a, dec + 1, dec + 1)
		i = i + 2
	end
	return res
end

savestate.loadslot(slot);
out = "raceid,ts,rs2,rs1,acc,coop,intel,stamina1,stamina2,sprinting,course,jockey,winorder,pos,name,rank,frame,random\n"
local thefile = "rank"..rank..".csv"

file = io.open(thefile,"a")
io.output(file)
io.write(out)
io.close()

local currentFrame = 1
local currentRandom = 0

local raceid = 0
local frameCount = 0
local step = 0
local pad = {}
local nclock = 0
while true do
	-- Code here will run once when the script is loaded, then after each emulated frame.
	if step == 0 then
		-- Random determines course
		memory.writebyte(0x095DC8, currentRandom)
		-- Frame determines chocos
		-- Convert number to u32
		memory.write_u32_le(0x051568,math.floor(currentFrame))
		console.log("Set Frame: " .. currentFrame .. " Random: " .. currentRandom)
		nclock = os.clock()
		step = 1
	end
	if step == 1 then	
		pad = {}
		if frameCount < 5 then
			pad['○'] = true
		elseif frameCount >= 600 and frameCount < 610 then
			pad['Start'] = true
		elseif frameCount >610 then
			console.log("Race started")
			step = 2
		end
		joypad.set(pad,1)
	end
	
	if step == 2 then
		if frameCount % 100 == 0 then
			local wbase = 0xB763C
			for i=0,5,1 do
				local winval = memory.readbyte(wbase+(i*0xa4))
				if winval == 6 then
					step = 3
					console.log("finish")
					break
				end
			end
		end
		--console.log("step 2") 
	end
	if step == 3 then
		local base1 = 0xB7654
		for i=0,5,1 do
			local base = base1+(i*0xa4)
			--console.log(base)
			local ts = memory.read_u16_le(base-48)
			local rs2 = memory.read_u16_le(base-50)
			local rs1 = memory.read_u16_le(base-58)
			local acc = memory.readbyte(base-42)
			local coop = memory.readbyte(base-38)
			local intel = memory.readbyte(base-36)
			local stamina2 = memory.read_u16_le(base-32)
			local stamina1 = memory.read_u16_le(base-28)
			local sprinting = memory.readbyte(base-60)
			local course = memory.read_u16_be(base-148)
			local jockey = memory.readbyte(base-130)
			local winorder = memory.readbyte(base-24)
			local pos = memory.readbyte(base-6)
			-- names are stored as big endian, even though the psx uses little endian
			local name = memory.read_u32_be(base)
			local name2 = memory.read_u16_be(base+4)
			local namec = decodeName(string.format('%X',name)) .. decodeName(string.format('%X',name2))
			local output = string.format("%d,%d,%d,%d,%X,%X,%X,%d,%d,%X,%X,%X,%X,%X,%s,%s,%d,%d\n", raceid, ts, rs2, rs1, acc, coop, intel, stamina1, stamina2, sprinting, course, jockey, winorder, pos, namec, rank, currentFrame, currentRandom)
			file = io.open(thefile,"a")
			io.output(file)
			io.write(output)
			io.close()
		end
		console.log(string.format("Finished - Frame:%d Course: %d", currentFrame, currentRandom))
		savestate.loadslot(slot);
		console.log("Time: " .. os.clock()-nclock)
		step = 0
		frameCount = 0
		raceid = raceid+1
		if currentRandom == 0 then
			-- 6 = short
			-- 0 = long
			currentRandom = 6
		else
			currentRandom = 0
			currentFrame = currentFrame+1
		end
		if rank == "c" then
			currentRandom = 0
			currentFrame = currentFrame+1
		end
	end
	frameCount = frameCount + 1
	emu.frameadvance();
	
end
