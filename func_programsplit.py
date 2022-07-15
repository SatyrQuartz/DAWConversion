
def add_to_seperated_object(seperated_object_table, objectdata, program):
    programfound = 0
    if seperated_object_table == []:
        seperated_object_table.append([program,[objectdata]])
    else:
        for prognote in seperated_object_table:
            if prognote[0] == program:
                programfound = 1
                prognote[1].append(objectdata)
        if programfound == 0:
            seperated_object_table.append([program,[objectdata]])

def seperate_program_placement_notelist(placement):
    seperated_notelist_table = []
    for note in placement['notelist']:
        copy_note = note.copy()
        program = copy_note['program']
        del copy_note['program']
        add_to_seperated_object(seperated_notelist_table, copy_note, program)
    return seperated_notelist_table

def seperate_program_placements(placement):
    global seperated_placement_table
    prognotetable = seperate_program_placement_notelist(placement)
    for prognote in prognotetable:
        program = prognote[0]
        notelist = prognote[1]
        placement_foroutput = placement.copy()
        del placement_foroutput['notelist']
        placement_foroutput['notelist'] = notelist
        add_to_seperated_object(seperated_placement_table, placement_foroutput, program)

def seperate_program_placements_get():
    return seperated_placement_table

def seperate_program_placements_init():
    global seperated_placement_table
    seperated_placement_table = []

def seperate_track_from_programs(track):
    seperate_program_placements_init()
    placements = track['placements']
    for placement in placements:
        seperate_program_placements(placement)
    seperated_placement_table = seperate_program_placements_get()
    out_tracks = []
    for seperated_placement in seperated_placement_table:
        out_track = track.copy()
        out_track['name'] = out_track['name'] + ';' + str(seperated_placement[0])
        out_track['placements'] = seperated_placement[1]
        out_track['internal_program'] = seperated_placement[0]
        out_tracks.append(out_track)
    return out_tracks
