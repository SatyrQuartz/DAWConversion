import json
import func_timednotes2listnotes
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("OpenMPT_pasted_in")
parser.add_argument("ConvProj_out")

args = parser.parse_args()

NoteLetters = ["C-","C#","D-","D#","E-","F-","F#","G-","G#","A-","A#","B-"]

global table_singlepattern
global ActiveNotes
global position
global output_noteslist
#ActiveNotes: Position,Duration,Note,velocity
ActiveNotes = []
output_noteslist = []
position = 0

def parse_omptcf_block(openmpt_block, firstrow):
	output_note = None
	output_inst = None
	output_modtype = None
	output_modvalue = None
	output_effect = None
	output_extra = {}
	openmpt_note = openmpt_block[0:3]
	openmpt_note_key = openmpt_note[0:2]
	openmpt_note_oct = openmpt_note[2:3]
	openmpt_inst = openmpt_block[3:5]
	openmpt_modtype = openmpt_block[5:6]
	openmpt_modvalue = openmpt_block[6:8]
	openmpt_effect = openmpt_block[8:11]
	#note
	if openmpt_note == '...':
		output_note = None
	elif openmpt_note == '~~~':
		output_note = 'Fade'
	elif openmpt_note == '^^^':
		output_note = 'Cut'
	elif openmpt_note == '===':
		output_note = 'Off'
	else:
		output_note = NoteLetters.index(openmpt_note_key) + int(openmpt_note_oct)*12 - 60
	#inst
	if openmpt_inst == '..':
		output_inst = None
	else:
		output_inst = int(openmpt_inst)
	#modtype
	if openmpt_modtype == 'v':
		output_modtype = 'vol'
	if openmpt_modtype == 'p':
		output_modtype = 'pan'
	#modtype
	if openmpt_modvalue != '..':
		output_modvalue = int(openmpt_modvalue)
		if openmpt_modtype == 'v':
			output_modvalue = output_modvalue/64
		if openmpt_modtype == 'p':
			output_modvalue = output_modvalue/32 - 0.5
	#modtype
	if openmpt_effect != '...':
		output_effect = openmpt_effect
	#modtype
	if firstrow == 1:
		output_extra['firstrow'] = 1
	return [output_note, output_inst, output_modtype, output_modvalue, output_effect, output_extra]

def parse_ompt_row(input_text_row, firstrow):
	global table_singlepattern
	global numofchannels
	input_row = input_text_row.strip().split("|")
	numofchannels = int(len(input_text_row.strip().split("|"))-1)
	table_row = []
	for input_block in input_row:
		if input_block != '':
			table_row.append(parse_omptcf_block(input_block, firstrow))
	table_singlepattern.append(table_row)

def parse_ompt_pasted_file(filename):
	global table_singlepattern
	global orders
	openmpt_copyfile = open(filename, 'r')
	openmpt_lines = openmpt_copyfile.readlines()
	table_patterns = []
	table_singlepattern = []

	started_patterndata = 0
	inside_pattern = 0
	rows_remaining = -1
	linenumber = 0
	first_row = 0
	for openmpt_line in openmpt_lines:
		linenumber += 1
		if inside_pattern == 1:
			parse_ompt_row(openmpt_line, first_row)
			first_row = 0
			rows_remaining -= 1
		if rows_remaining <= 0:
			inside_pattern = 0
		if linenumber == 1:
			placeholder = 0
		if linenumber == 2:
			orders = openmpt_line.strip().split(': ')[1].split(',')
		if 'Rows:' in openmpt_line:
			if started_patterndata == 1:
				table_patterns.append(table_singlepattern)
			first_row = 1
			started_patterndata = 1
			table_singlepattern = []
			inside_pattern = 1
			rows_remaining = int(openmpt_line.strip().split(':')[1])
		#print('LINE: ' + str(linenumber) + ' ROW: ' + str(rows_remaining) + ' ' + openmpt_line.strip())
	if table_singlepattern is not []:
		table_patterns.append(table_singlepattern)
	return table_patterns

def get_channeldata_inside_pattern(patternstable, pattern, channel):
	output_table = []
	position = 0
	patternsize = len(patternstable[pattern])
	while position < patternsize:
		output_table.append(patternstable[pattern][position][channel])
		position += 1
	return output_table

def entire_song_channel(patternstable, channel):
	entire_song_channel = []
	for specificpattern in orders:
		if specificpattern != '+':
			patterndata = get_channeldata_inside_pattern(patternstable,int(specificpattern),channel)
			for patternrow in patterndata:
				entire_song_channel.append(patternrow)
	return entire_song_channel

def convertchannel2timednotes(channelsong, tickrow):
	tickrowfinal = tickrow/6
	output_channel = []
	note_held = 0
	current_inst = None
	current_key = None
	first_seperate = 0
	for notecommand in channelsong:
		if notecommand[0] == None:
			if 'firstrow' in notecommand[5]:
				if first_seperate == 1:
					output_channel.append('seperate;')
				if first_seperate == 0:
					first_seperate = 1
			output_channel.append('break;' + str(tickrowfinal))
		elif notecommand[0] == 'Fade' or notecommand[0] == 'Cut' or notecommand[0] == 'Off':
			if note_held == 1:
				output_channel.append('note_off;' + str(current_key))
			note_held = 0
			if 'firstrow' in notecommand[5]:
				if first_seperate == 1:
					output_channel.append('seperate;')
				if first_seperate == 0:
					first_seperate = 1
			output_channel.append('break;' + str(tickrowfinal))
		else:
			if note_held == 1:
				output_channel.append('note_off;' + str(current_key))
			if 'firstrow' in notecommand[5]:
				if first_seperate == 1:
					output_channel.append('seperate;')
				if first_seperate == 0:
					first_seperate = 1
			if current_inst != notecommand[1] and isinstance(notecommand[1], int):
				output_channel.append('program;' + str(notecommand[1]))
				current_inst = notecommand[1]
			note_held = 1
			current_key = notecommand[0]
			volume = 1.0
			if notecommand[2] == "vol":
				volume = notecommand[3]
			output_channel.append('note_on;' + str(notecommand[0])+','+str(volume))
			output_channel.append('break;' + str(tickrowfinal))
	return output_channel

patternstable = parse_ompt_pasted_file(args.OpenMPT_pasted_in)
tickrow = 3

tracks = []

for channelnum in range(numofchannels):
	func_timednotes2listnotes.tm2nlp_track_start()
	channelsong = entire_song_channel(patternstable,channelnum)
	timednotes = convertchannel2timednotes(channelsong, tickrow)
	singletrack = {}
	singletrack['instrumentdata'] = {"plugindata": {},"usemasterpitch": 1,"pitch": 0.0,"basenote": 60,"plugin": "none"}
	singletrack['name'] = "channel"
	singletrack['muted'] = 0
	singletrack['pan'] = 0.0
	singletrack['vol'] = 0.3
	singletrack['type'] = "instrument"
	singletrack['placements'] = func_timednotes2listnotes.tm2nlp_parse_timednotes(timednotes)
	tracks.append(singletrack)

mainjson = {}

mainjson['mastervol'] = 1.0
mainjson['masterpitch'] = 0.0
mainjson['timesig_numerator'] = 4.0
mainjson['timesig_denominator'] = 4.0
mainjson['bpm'] = 140.0
mainjson['tracks'] = tracks

with open(args.ConvProj_out, 'w') as f:
    json.dump(mainjson, f)
