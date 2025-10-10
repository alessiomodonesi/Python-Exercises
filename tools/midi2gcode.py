from mido import MidiFile

def note_to_freq(note):
    """Convert MIDI note (0-127) to frequency in Hz"""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def midi_to_gcode(midi_path, gcode_path, channel=0):
    mid = MidiFile(midi_path)
    ticks_per_beat = mid.ticks_per_beat

    tempo = 500000  # default 120 BPM (500k µs per beat)
    time_ms_per_tick = tempo / ticks_per_beat / 1000.0

    gcode_lines = ["; ==== START MIDI TO GCODE ====", "M17"]

    current_time = 0
    note_on_time = {}

    for track in mid.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                time_ms_per_tick = tempo / ticks_per_beat / 1000.0

            elif msg.type == 'note_on' and msg.channel == channel and msg.velocity > 0:
                note_on_time[msg.note] = abs_time

            elif (msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)) and msg.channel == channel:
                if msg.note in note_on_time:
                    start_tick = note_on_time.pop(msg.note)
                    dur_ticks = abs_time - start_tick
                    dur_ms = int(dur_ticks * time_ms_per_tick)
                    freq = int(note_to_freq(msg.note))
                    if dur_ms > 0:
                        gcode_lines.append(f"M300 S{freq} P{dur_ms}")
                        gcode_lines.append("M300 S0 P30")  # small pause

    gcode_lines.append("M18")
    gcode_lines.append("; ==== END MIDI TO GCODE ====")

    with open(gcode_path, "w") as f:
        f.write("\n".join(gcode_lines))

# USO
midi_to_gcode("input.mid", "output.gcode")
