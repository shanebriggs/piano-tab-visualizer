import streamlit as st
import docx
import re

# 1. THE CHORD ENGINE (Mathematical Voicing)
def calculate_voicing(chord_str):
    """Calculates a 4-to-5 note piano voicing for ANY given chord string."""
    SVG_NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]
    
    def get_note_index(note_name):
        mapping = {'C':0, 'C#':1, 'Db':1, 'D':2, 'D#':3, 'Eb':3, 'E':4, 'F':5, 
                   'F#':6, 'Gb':6, 'G':7, 'G#':8, 'Ab':8, 'A':9, 'A#':10, 'Bb':10, 'B':11}
        return mapping.get(note_name, 0)

    # Clean the chord string: Remove anything inside parentheses for the calculation
    calc_chord = re.sub(r'\(.*?\)', '', chord_str)
    parts = calc_chord.split('/')
    base_chord = parts[0]
    bass_note = parts[1] if len(parts) > 1 else None

    # Extract Root and Quality
    match = re.match(r"^([A-G][b#]?)(.*)", base_chord)
    if not match: return []
    
    root_note = match.group(1)
    quality = match.group(2).lower()
    root_idx = get_note_index(root_note)

    # Calculate Intervals
    intervals = set([0]) 
    if 'm' in quality and 'maj' not in quality: intervals.add(3)
    elif 'sus2' in quality: intervals.add(2)
    elif 'sus4' in quality or ('sus' in quality and 'sus2' not in quality): intervals.add(5)
    else: intervals.add(4)
        
    if 'maj7' in quality or 'maj9' in quality or 'maj13' in quality: intervals.add(11)
    elif '7' in quality or '9' in quality or '11' in quality or '13' in quality: intervals.add(10)
    elif 'dim7' in quality: intervals.add(9)
        
    if '9' in quality: intervals.add(14)
    if '13' in quality: intervals.add(21)
    if '6' in quality: intervals.add(9)
    if 'dim' in quality: intervals.add(6)
    if 'aug' in quality: intervals.add(8)
    
    if len(intervals) < 4 and 'dim' not in quality and 'aug' not in quality: intervals.add(7)

    note_names = [SVG_NOTES[(root_idx + iv) % 12] for iv in sorted(list(intervals))]
    
    actual_bass = bass_note if bass_note else root_note
    actual_bass_svg = SVG_NOTES[get_note_index(actual_bass)]
    
    voicing = [f"{actual_bass_svg}2"]
    notes_added = 0
    for note in note_names:
        if note != actual_bass_svg or len(voicing) == 0:
            octave = "3" if notes_added < 3 else "4"
            voicing.append(f"{note}{octave}")
            notes_added += 1
    return voicing

# 2. APP INTERFACE
st.title("Piano Tab Visualizer")
uploaded_file = st.file_uploader("Upload Word (.docx) Tab", type=["docx"])

if uploaded_file:
    doc = docx.Document(uploaded_file)
    sequence = []
    chord_pattern = re.compile(r"^[A-G][#b]?(m|maj|min|M|sus|dim|aug|add)?[0-9]*(\(.*?\))?(sus[0-9]*)?(/[A-G][#b]?)?$", re.IGNORECASE)

    def is_chord_line(text):
        words = text.split()
        return words and all(chord_pattern.match(w.strip(".,;")) for w in words)

    pars = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for i, text in enumerate(pars):
        if is_chord_line(text):
            chords = [w.strip(".,;") for w in text.split()]
            lyric = pars[i+1] if i+1 < len(pars) and not is_chord_line(pars[i+1]) and not pars[i+1].lower().startswith(("intro", "verse", "chorus")) else ""
            for chord in chords:
                sequence.append({"chord": chord, "lyric": lyric, "keys": calculate_voicing(chord)})

    # UI Logic
    if 'step' not in st.session_state: st.session_state.step = 0
    
    col1, col2 = st.columns(2)
    if col1.button("Previous"): st.session_state.step = max(0, st.session_state.step - 1)
    if col2.button("Next"): st.session_state.step = min(len(sequence)-1, st.session_state.step + 1)
    
    if sequence:
        data = sequence[st.session_state.step]
        st.markdown(f"### {data['lyric']}")
        st.markdown(f"## {data['chord']} <span style='font-size: 14px; font-weight: normal; color: #888;'>({st.session_state.step + 1}/{len(sequence)})</span>", unsafe_allow_html=True)
        
        # SVG PIANO (With corrected layering)
        active = data['keys']
        svg = ['<svg width="100%" height="150" style="border:1px solid #ccc; background:#fff;">']
        
        # 1. White keys
        x = 0
        for oct in ["2", "3", "4"]:
            for n in ["C", "D", "E", "F", "G", "A", "B"]:
                f = "lightblue" if f"{n}{oct}" in active else "white"
                svg.append(f'<rect x="{x}" y="0" width="40" height="150" fill="{f}" stroke="black" stroke-width="1" />')
                x += 40
        
        # 2. Black keys (drawn last to sit on top)
        black_offsets = {"C#": 30, "Eb": 70, "F#": 150, "G#": 190, "Bb": 230}
        x_start = 0
        for oct in ["2", "3", "4"]:
            for note, offset in black_offsets.items():
                f = "lightblue" if f"{note}{oct}" in active else "black"
                svg.append(f'<rect x="{x_start + offset}" y="0" width="25" height="90" fill="{f}" stroke="black" stroke-width="1" />')
            x_start += 280
            
        svg.append('</svg>')
        st.write("".join(svg), unsafe_allow_html=True)
