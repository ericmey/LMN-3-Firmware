"""
LMN-3 Firmware MIDI Specification

Ground truth from:
- /Users/ericmey/Projects/LMN-3-Firmware/src/config.h
- /Users/ericmey/Projects/LMN-3-Firmware/src/main.cpp

MIDI Channel: 1 (Channel_1 in firmware)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

# MIDI Channel (0-indexed for mido, 1-indexed in firmware)
MIDI_CHANNEL = 0  # Channel_1 in firmware = channel 0 in mido

# Encoder CC Numbers (rotation)
ENCODER_1 = 3
ENCODER_2 = 9
ENCODER_3 = 14
ENCODER_4 = 15

# Encoder Button CC Numbers
ENCODER_1_BUTTON = 20
ENCODER_2_BUTTON = 21
ENCODER_3_BUTTON = 22
ENCODER_4_BUTTON = 23

# Transport/Edit CC Numbers
UNDO_BUTTON = 24
TEMPO_BUTTON = 25
SAVE_BUTTON = 26
SETTINGS_BUTTON = 85  # SET in visual layout
TRACKS_BUTTON = 86
MIXER_BUTTON = 88
PLUGINS_BUTTON = 89
MODIFIERS_BUTTON = 90  # MODS in visual layout
SEQUENCERS_BUTTON = 102  # SEQ in visual layout
LOOP_IN_BUTTON = 103
LOOP_OUT_BUTTON = 104
LOOP_BUTTON = 105
CUT_BUTTON = 106
PASTE_BUTTON = 107
SLICE_BUTTON = 108
RECORD_BUTTON = 109
PLAY_BUTTON = 110
STOP_BUTTON = 111
CONTROL_BUTTON = 112  # CTRL in visual layout

# Special Controls
OCTAVE_CHANGE = 117  # Values 0-8 (transposition + 4)
PLUS_BUTTON = 118
MINUS_BUTTON = 119
DUMMY = 31  # Disabled positions - should be ignored

# Encoder rotation values (relative mode)
ENCODER_INCREMENT = 1
ENCODER_DECREMENT = 127

# Button values
BUTTON_PRESSED = 127
BUTTON_RELEASED = 0

# Octave range
MIN_OCTAVE = 0  # Represents -4 octaves
MAX_OCTAVE = 8  # Represents +4 octaves
DEFAULT_OCTAVE = 4  # Represents 0 octaves

# Note matrix (2x14) - Rows 3-4 in hardware, value 1 = disabled
# Row 3 (black keys pattern with gaps)
NOTE_ROW_3 = [1, 54, 56, 58, 1, 61, 63, 1, 66, 68, 70, 1, 73, 75]
# Row 4 (chromatic white keys)
NOTE_ROW_4 = [53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74, 76]

# Valid note range (before transposition)
MIN_NOTE = 53
MAX_NOTE = 76
# Transposition range: ±4 octaves = ±48 semitones
TRANSPOSITION_RANGE = 48


class ComponentType(Enum):
    ENCODER_ROTATION = "encoder_rotation"
    ENCODER_BUTTON = "encoder_button"
    TRANSPORT_BUTTON = "transport_button"
    EDIT_BUTTON = "edit_button"
    SPECIAL_CONTROL = "special_control"
    NOTE = "note"
    PITCH_BEND = "pitch_bend"
    DUMMY = "dummy"


@dataclass
class ComponentSpec:
    """Specification for a single hardware component"""
    name: str
    component_type: ComponentType
    cc_number: Optional[int] = None  # For CC-based controls
    note_number: Optional[int] = None  # For note-based controls
    row: Optional[int] = None  # Grid row position
    col: Optional[int] = None  # Grid column position
    valid_values: Optional[tuple] = None  # Expected value range/set


# All CC-based components
CC_COMPONENTS = {
    # Encoder rotations
    ENCODER_1: ComponentSpec("ENC1", ComponentType.ENCODER_ROTATION, cc_number=ENCODER_1,
                             row=0, col=9, valid_values=(1, 127)),
    ENCODER_2: ComponentSpec("ENC2", ComponentType.ENCODER_ROTATION, cc_number=ENCODER_2,
                             row=0, col=10, valid_values=(1, 127)),
    ENCODER_3: ComponentSpec("ENC3", ComponentType.ENCODER_ROTATION, cc_number=ENCODER_3,
                             row=0, col=12, valid_values=(1, 127)),
    ENCODER_4: ComponentSpec("ENC4", ComponentType.ENCODER_ROTATION, cc_number=ENCODER_4,
                             row=0, col=13, valid_values=(1, 127)),

    # Encoder buttons
    ENCODER_1_BUTTON: ComponentSpec("ENC1_BTN", ComponentType.ENCODER_BUTTON, cc_number=ENCODER_1_BUTTON,
                                    row=0, col=9, valid_values=(0, 127)),
    ENCODER_2_BUTTON: ComponentSpec("ENC2_BTN", ComponentType.ENCODER_BUTTON, cc_number=ENCODER_2_BUTTON,
                                    row=0, col=10, valid_values=(0, 127)),
    ENCODER_3_BUTTON: ComponentSpec("ENC3_BTN", ComponentType.ENCODER_BUTTON, cc_number=ENCODER_3_BUTTON,
                                    row=0, col=12, valid_values=(0, 127)),
    ENCODER_4_BUTTON: ComponentSpec("ENC4_BTN", ComponentType.ENCODER_BUTTON, cc_number=ENCODER_4_BUTTON,
                                    row=0, col=13, valid_values=(0, 127)),

    # Transport/Edit buttons (Row 0)
    LOOP_BUTTON: ComponentSpec("LOOP", ComponentType.TRANSPORT_BUTTON, cc_number=LOOP_BUTTON,
                               row=0, col=3, valid_values=(0, 127)),
    LOOP_IN_BUTTON: ComponentSpec("LOOP_IN", ComponentType.TRANSPORT_BUTTON, cc_number=LOOP_IN_BUTTON,
                                  row=0, col=4, valid_values=(0, 127)),
    LOOP_OUT_BUTTON: ComponentSpec("LOOP_OUT", ComponentType.TRANSPORT_BUTTON, cc_number=LOOP_OUT_BUTTON,
                                   row=0, col=5, valid_values=(0, 127)),

    # Edit buttons (Row 1)
    CUT_BUTTON: ComponentSpec("CUT", ComponentType.EDIT_BUTTON, cc_number=CUT_BUTTON,
                              row=1, col=3, valid_values=(0, 127)),
    PASTE_BUTTON: ComponentSpec("PASTE", ComponentType.EDIT_BUTTON, cc_number=PASTE_BUTTON,
                                row=1, col=4, valid_values=(0, 127)),
    SLICE_BUTTON: ComponentSpec("SLICE", ComponentType.EDIT_BUTTON, cc_number=SLICE_BUTTON,
                                row=1, col=5, valid_values=(0, 127)),
    SAVE_BUTTON: ComponentSpec("SAVE", ComponentType.EDIT_BUTTON, cc_number=SAVE_BUTTON,
                               row=1, col=6, valid_values=(0, 127)),
    UNDO_BUTTON: ComponentSpec("UNDO", ComponentType.EDIT_BUTTON, cc_number=UNDO_BUTTON,
                               row=1, col=7, valid_values=(0, 127)),

    # Transport/Navigation buttons (Row 2)
    CONTROL_BUTTON: ComponentSpec("CTRL", ComponentType.TRANSPORT_BUTTON, cc_number=CONTROL_BUTTON,
                                  row=2, col=3, valid_values=(0, 127)),
    RECORD_BUTTON: ComponentSpec("REC", ComponentType.TRANSPORT_BUTTON, cc_number=RECORD_BUTTON,
                                 row=2, col=4, valid_values=(0, 127)),
    PLAY_BUTTON: ComponentSpec("PLAY", ComponentType.TRANSPORT_BUTTON, cc_number=PLAY_BUTTON,
                               row=2, col=5, valid_values=(0, 127)),
    STOP_BUTTON: ComponentSpec("STOP", ComponentType.TRANSPORT_BUTTON, cc_number=STOP_BUTTON,
                               row=2, col=6, valid_values=(0, 127)),
    SETTINGS_BUTTON: ComponentSpec("SET", ComponentType.TRANSPORT_BUTTON, cc_number=SETTINGS_BUTTON,
                                   row=2, col=7, valid_values=(0, 127)),
    TEMPO_BUTTON: ComponentSpec("TEMPO", ComponentType.TRANSPORT_BUTTON, cc_number=TEMPO_BUTTON,
                                row=2, col=8, valid_values=(0, 127)),
    MIXER_BUTTON: ComponentSpec("MIXER", ComponentType.TRANSPORT_BUTTON, cc_number=MIXER_BUTTON,
                                row=2, col=9, valid_values=(0, 127)),
    TRACKS_BUTTON: ComponentSpec("TRACKS", ComponentType.TRANSPORT_BUTTON, cc_number=TRACKS_BUTTON,
                                 row=2, col=10, valid_values=(0, 127)),
    PLUGINS_BUTTON: ComponentSpec("PLUGINS", ComponentType.TRANSPORT_BUTTON, cc_number=PLUGINS_BUTTON,
                                  row=2, col=11, valid_values=(0, 127)),
    MODIFIERS_BUTTON: ComponentSpec("MODS", ComponentType.TRANSPORT_BUTTON, cc_number=MODIFIERS_BUTTON,
                                    row=2, col=12, valid_values=(0, 127)),
    SEQUENCERS_BUTTON: ComponentSpec("SEQ", ComponentType.TRANSPORT_BUTTON, cc_number=SEQUENCERS_BUTTON,
                                     row=2, col=13, valid_values=(0, 127)),

    # Special controls
    PLUS_BUTTON: ComponentSpec("PLUS", ComponentType.SPECIAL_CONTROL, cc_number=PLUS_BUTTON,
                               row=0, col=6, valid_values=(0, 127)),
    MINUS_BUTTON: ComponentSpec("MINUS", ComponentType.SPECIAL_CONTROL, cc_number=MINUS_BUTTON,
                                row=0, col=7, valid_values=(0, 127)),
    OCTAVE_CHANGE: ComponentSpec("OCTAVE", ComponentType.SPECIAL_CONTROL, cc_number=OCTAVE_CHANGE,
                                 valid_values=tuple(range(9))),  # 0-8

    # Dummy (disabled positions)
    DUMMY: ComponentSpec("DUMMY", ComponentType.DUMMY, cc_number=DUMMY),
}

# CC Address matrix (3x11) - Rows 0-2, Columns 3-13
# Mirrors the firmware ccAddresses matrix
CC_MATRIX = [
    # Row 0: LOOP controls + encoders
    [LOOP_BUTTON, LOOP_IN_BUTTON, LOOP_OUT_BUTTON, DUMMY, DUMMY, DUMMY,
     ENCODER_1_BUTTON, ENCODER_2_BUTTON, DUMMY, ENCODER_3_BUTTON, ENCODER_4_BUTTON],
    # Row 1: Edit controls
    [CUT_BUTTON, PASTE_BUTTON, SLICE_BUTTON, SAVE_BUTTON, UNDO_BUTTON,
     DUMMY, DUMMY, DUMMY, DUMMY, DUMMY, DUMMY],
    # Row 2: Transport/navigation
    [CONTROL_BUTTON, RECORD_BUTTON, PLAY_BUTTON, STOP_BUTTON, SETTINGS_BUTTON,
     TEMPO_BUTTON, MIXER_BUTTON, TRACKS_BUTTON, PLUGINS_BUTTON, MODIFIERS_BUTTON, SEQUENCERS_BUTTON],
]

# Note matrix (2x14) - Rows 3-4, Columns 0-13
# Value 1 = disabled position
NOTE_MATRIX = [
    NOTE_ROW_3,  # Row 3: Black keys with gaps
    NOTE_ROW_4,  # Row 4: White keys (chromatic)
]


def get_all_valid_cc_numbers() -> set:
    """Return set of all valid CC numbers (excluding DUMMY)"""
    return {cc for cc in CC_COMPONENTS.keys() if cc != DUMMY}


def get_all_valid_notes() -> set:
    """Return set of all valid note numbers from the matrix"""
    notes = set()
    for row in NOTE_MATRIX:
        for note in row:
            if note != 1:  # 1 = disabled
                notes.add(note)
    return notes


def get_encoder_ccs() -> set:
    """Return set of encoder rotation CC numbers"""
    return {ENCODER_1, ENCODER_2, ENCODER_3, ENCODER_4}


def get_encoder_button_ccs() -> set:
    """Return set of encoder button CC numbers"""
    return {ENCODER_1_BUTTON, ENCODER_2_BUTTON, ENCODER_3_BUTTON, ENCODER_4_BUTTON}


def is_valid_encoder_value(value: int) -> bool:
    """Check if value is valid for encoder rotation (1=CW, 127=CCW)"""
    return value in (ENCODER_INCREMENT, ENCODER_DECREMENT)


def is_valid_button_value(value: int) -> bool:
    """Check if value is valid for button press/release"""
    return value in (BUTTON_PRESSED, BUTTON_RELEASED)


def is_valid_octave_value(value: int) -> bool:
    """Check if value is valid for octave change (0-8)"""
    return MIN_OCTAVE <= value <= MAX_OCTAVE


def octave_value_to_semitones(value: int) -> int:
    """Convert octave MIDI value (0-8) to semitone offset (-48 to +48)"""
    return (value - DEFAULT_OCTAVE) * 12


def is_valid_note(note: int, transposition: int = 0) -> bool:
    """Check if note is valid considering transposition"""
    base_notes = get_all_valid_notes()
    # Check if note could be a transposed version of any base note
    for base_note in base_notes:
        if note == base_note + transposition:
            return True
    return False


def get_component_by_cc(cc_number: int) -> Optional[ComponentSpec]:
    """Get component specification by CC number"""
    return CC_COMPONENTS.get(cc_number)


def get_component_name(cc_number: int) -> str:
    """Get human-readable component name by CC number"""
    comp = CC_COMPONENTS.get(cc_number)
    return comp.name if comp else f"CC#{cc_number}"


# Total testable components (excluding DUMMY positions and pitch bend)
def get_total_testable_components() -> int:
    """
    Calculate total number of testable components:
    - 4 encoder rotations
    - 4 encoder buttons
    - 21 CC buttons (excluding DUMMY positions)
    - 2 special controls (PLUS, MINUS)
    - 1 OCTAVE_CHANGE
    - 24 notes (excluding disabled positions)
    - 1 pitch bend
    """
    # Count unique CC components (not DUMMY)
    cc_count = len([c for c in CC_COMPONENTS.values()
                    if c.component_type != ComponentType.DUMMY])
    # Count valid notes
    note_count = len(get_all_valid_notes())
    # Add pitch bend
    pitch_bend_count = 1

    return cc_count + note_count + pitch_bend_count


# Component groups for UI display
COMPONENT_GROUPS = {
    "Encoders": [ENCODER_1, ENCODER_2, ENCODER_3, ENCODER_4],
    "Enc Buttons": [ENCODER_1_BUTTON, ENCODER_2_BUTTON, ENCODER_3_BUTTON, ENCODER_4_BUTTON],
    "Loop": [LOOP_BUTTON, LOOP_IN_BUTTON, LOOP_OUT_BUTTON],
    "Edit": [CUT_BUTTON, PASTE_BUTTON, SLICE_BUTTON, SAVE_BUTTON, UNDO_BUTTON],
    "Transport": [CONTROL_BUTTON, RECORD_BUTTON, PLAY_BUTTON, STOP_BUTTON],
    "Navigation": [SETTINGS_BUTTON, TEMPO_BUTTON, MIXER_BUTTON, TRACKS_BUTTON,
                   PLUGINS_BUTTON, MODIFIERS_BUTTON, SEQUENCERS_BUTTON],
    "Special": [PLUS_BUTTON, MINUS_BUTTON, OCTAVE_CHANGE],
}
