"""
Board Canvas for LMN-3 Tester

tkinter Canvas-based visual representation of the LMN-3 board.
Displays buttons, encoders, piano keys, and pitch bend with
color-coded test status indicators.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, Callable
from dataclasses import dataclass

from firmware_spec import (
    CC_COMPONENTS, ComponentType, NOTE_MATRIX,
    ENCODER_1, ENCODER_2, ENCODER_3, ENCODER_4,
    ENCODER_1_BUTTON, ENCODER_2_BUTTON, ENCODER_3_BUTTON, ENCODER_4_BUTTON,
    LOOP_BUTTON, LOOP_IN_BUTTON, LOOP_OUT_BUTTON,
    CUT_BUTTON, PASTE_BUTTON, SLICE_BUTTON, SAVE_BUTTON, UNDO_BUTTON,
    CONTROL_BUTTON, RECORD_BUTTON, PLAY_BUTTON, STOP_BUTTON,
    SETTINGS_BUTTON, TEMPO_BUTTON, MIXER_BUTTON, TRACKS_BUTTON,
    PLUGINS_BUTTON, MODIFIERS_BUTTON, SEQUENCERS_BUTTON,
    PLUS_BUTTON, MINUS_BUTTON, get_all_valid_notes
)


@dataclass
class VisualState:
    """Visual state for a component"""
    tested: bool = False
    valid: bool = False
    active: bool = False  # Currently pressed/active


class Colors:
    """Color constants for visual states"""
    UNTESTED = "#808080"  # Gray
    VALID = "#4CAF50"  # Green
    INVALID = "#F44336"  # Red
    ACTIVE = "#FFC107"  # Yellow/Amber
    WARNING = "#FF9800"  # Orange
    BACKGROUND = "#2D2D2D"  # Dark gray
    TEXT = "#FFFFFF"  # White
    TEXT_DARK = "#000000"  # Black
    BORDER = "#555555"  # Medium gray
    WHITE_KEY = "#FAFAFA"
    BLACK_KEY = "#1A1A1A"


class BoardCanvas(tk.Frame):
    """
    Visual representation of the LMN-3 board using tkinter Canvas.

    Displays:
    - Button grid (rows 0-2)
    - Encoder knobs with buttons
    - Piano keys (rows 3-4)
    - Pitch bend joystick indicator
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=Colors.BACKGROUND)

        # Canvas dimensions
        self.canvas_width = 800
        self.canvas_height = 400

        # Component visual elements (canvas item IDs)
        self._cc_items: Dict[int, int] = {}  # CC number -> canvas item ID
        self._note_items: Dict[int, int] = {}  # Note number -> canvas item ID
        self._pitch_bend_item: Optional[int] = None
        self._pitch_bend_indicator: Optional[int] = None

        # Visual states
        self._cc_states: Dict[int, VisualState] = {}
        self._note_states: Dict[int, VisualState] = {}
        self._pitch_bend_state = VisualState()

        # Create canvas
        self.canvas = tk.Canvas(
            self,
            width=self.canvas_width,
            height=self.canvas_height,
            bg=Colors.BACKGROUND,
            highlightthickness=0
        )
        self.canvas.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self._create_board_layout()

    def _create_board_layout(self):
        """Create all visual elements for the board"""
        # Layout constants
        button_width = 45
        button_height = 35
        button_spacing = 5
        start_x = 20
        start_y = 20

        # Row 0: Loop buttons + Plus/Minus + Encoders
        y = start_y
        x = start_x

        # Loop buttons
        for cc, label in [(LOOP_BUTTON, "LOOP"), (LOOP_IN_BUTTON, "IN"), (LOOP_OUT_BUTTON, "OUT")]:
            self._create_button(x, y, button_width, button_height, cc, label)
            x += button_width + button_spacing

        # Gap
        x += 20

        # Plus/Minus
        for cc, label in [(PLUS_BUTTON, "+"), (MINUS_BUTTON, "-")]:
            self._create_button(x, y, 30, button_height, cc, label)
            x += 30 + button_spacing

        # Gap before encoders
        x += 30

        # Encoders (with buttons)
        encoder_pairs = [
            (ENCODER_1, ENCODER_1_BUTTON, "E1"),
            (ENCODER_2, ENCODER_2_BUTTON, "E2"),
            (ENCODER_3, ENCODER_3_BUTTON, "E3"),
            (ENCODER_4, ENCODER_4_BUTTON, "E4"),
        ]
        encoder_size = 40
        for enc_cc, btn_cc, label in encoder_pairs:
            self._create_encoder(x, y, encoder_size, enc_cc, btn_cc, label)
            x += encoder_size + button_spacing * 2

        # Row 1: Edit buttons
        y += button_height + button_spacing + 15
        x = start_x

        for cc, label in [
            (CUT_BUTTON, "CUT"), (PASTE_BUTTON, "PASTE"), (SLICE_BUTTON, "SLICE"),
            (SAVE_BUTTON, "SAVE"), (UNDO_BUTTON, "UNDO")
        ]:
            self._create_button(x, y, button_width, button_height, cc, label)
            x += button_width + button_spacing

        # Row 2: Transport/Navigation buttons
        y += button_height + button_spacing + 10
        x = start_x

        for cc, label in [
            (CONTROL_BUTTON, "CTRL"), (RECORD_BUTTON, "REC"), (PLAY_BUTTON, "PLAY"),
            (STOP_BUTTON, "STOP"), (SETTINGS_BUTTON, "SET"), (TEMPO_BUTTON, "TEMPO"),
            (MIXER_BUTTON, "MIX"), (TRACKS_BUTTON, "TRKS"), (PLUGINS_BUTTON, "PLUG"),
            (MODIFIERS_BUTTON, "MODS"), (SEQUENCERS_BUTTON, "SEQ")
        ]:
            self._create_button(x, y, button_width, button_height, cc, label)
            x += button_width + button_spacing

        # Piano keys (Rows 3-4)
        y += button_height + button_spacing + 20
        self._create_piano_keys(start_x, y)

        # Pitch bend joystick
        self._create_pitch_bend(start_x + 550, y + 30)

    def _create_button(self, x: int, y: int, width: int, height: int,
                       cc_num: int, label: str):
        """Create a button visual element"""
        # Get CC number for display
        rect = self.canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=Colors.UNTESTED,
            outline=Colors.BORDER,
            width=1
        )

        # Label
        self.canvas.create_text(
            x + width / 2, y + height / 2 - 5,
            text=label,
            fill=Colors.TEXT,
            font=("Helvetica", 8, "bold")
        )

        # CC number
        self.canvas.create_text(
            x + width / 2, y + height / 2 + 8,
            text=str(cc_num),
            fill=Colors.TEXT,
            font=("Helvetica", 7)
        )

        self._cc_items[cc_num] = rect
        self._cc_states[cc_num] = VisualState()

    def _create_encoder(self, x: int, y: int, size: int,
                        rotation_cc: int, button_cc: int, label: str):
        """Create an encoder visual element (circle with inner button)"""
        # Outer circle (rotation indicator)
        outer = self.canvas.create_oval(
            x, y, x + size, y + size,
            fill=Colors.UNTESTED,
            outline=Colors.BORDER,
            width=2
        )

        # Inner circle (button)
        inner_size = size * 0.5
        inner_offset = (size - inner_size) / 2
        inner = self.canvas.create_oval(
            x + inner_offset, y + inner_offset,
            x + inner_offset + inner_size, y + inner_offset + inner_size,
            fill=Colors.UNTESTED,
            outline=Colors.BORDER,
            width=1
        )

        # Label above
        self.canvas.create_text(
            x + size / 2, y - 8,
            text=label,
            fill=Colors.TEXT,
            font=("Helvetica", 9, "bold")
        )

        # CC numbers below
        self.canvas.create_text(
            x + size / 2, y + size + 10,
            text=f"{rotation_cc}/{button_cc}",
            fill=Colors.TEXT,
            font=("Helvetica", 7)
        )

        self._cc_items[rotation_cc] = outer
        self._cc_items[button_cc] = inner
        self._cc_states[rotation_cc] = VisualState()
        self._cc_states[button_cc] = VisualState()

    def _create_piano_keys(self, start_x: int, start_y: int):
        """Create piano key visualizations"""
        # Piano layout based on note matrix
        # Row 4 (white keys): 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74, 76
        # Row 3 (black keys): gaps at positions 0, 4, 7, 11

        white_key_width = 30
        white_key_height = 60
        black_key_width = 20
        black_key_height = 35

        # White keys (Row 4)
        white_notes = NOTE_MATRIX[1]  # [53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72, 74, 76]
        x = start_x
        for note in white_notes:
            rect = self.canvas.create_rectangle(
                x, start_y, x + white_key_width, start_y + white_key_height,
                fill=Colors.WHITE_KEY,
                outline=Colors.BORDER,
                width=1
            )
            # Note number at bottom
            self.canvas.create_text(
                x + white_key_width / 2, start_y + white_key_height - 10,
                text=str(note),
                fill=Colors.TEXT_DARK,
                font=("Helvetica", 7)
            )
            self._note_items[note] = rect
            self._note_states[note] = VisualState()
            x += white_key_width + 2

        # Black keys (Row 3) - positioned above white keys
        black_notes = NOTE_MATRIX[0]  # [1, 54, 56, 58, 1, 61, 63, 1, 66, 68, 70, 1, 73, 75]
        black_key_y = start_y - 5

        # Black key positions relative to white keys
        # Black keys appear between certain white keys
        black_positions = [
            (0.7, 54), (1.7, 56), (2.7, 58),  # C#, D#, E# (F)
            (4.7, 61), (5.7, 63),  # G#, A#
            (7.7, 66), (8.7, 68), (9.7, 70),  # C#, D#, E#
            (11.7, 73), (12.7, 75),  # G#, A#
        ]

        for pos, note in black_positions:
            if note == 1:
                continue  # Skip disabled positions
            bx = start_x + pos * (white_key_width + 2) - black_key_width / 2
            rect = self.canvas.create_rectangle(
                bx, black_key_y, bx + black_key_width, black_key_y + black_key_height,
                fill=Colors.BLACK_KEY,
                outline=Colors.BORDER,
                width=1
            )
            self._note_items[note] = rect
            self._note_states[note] = VisualState()

        # Label
        self.canvas.create_text(
            start_x + 200, start_y + white_key_height + 15,
            text="Notes 53-76 (transposition: \u00b14 octaves)",
            fill=Colors.TEXT,
            font=("Helvetica", 9)
        )

    def _create_pitch_bend(self, x: int, y: int):
        """Create pitch bend joystick visualization"""
        # Outer track
        track_width = 120
        track_height = 30

        self.canvas.create_rectangle(
            x, y, x + track_width, y + track_height,
            fill=Colors.BACKGROUND,
            outline=Colors.BORDER,
            width=2
        )

        # Center line
        center_x = x + track_width / 2
        self.canvas.create_line(
            center_x, y, center_x, y + track_height,
            fill=Colors.BORDER,
            width=1,
            dash=(2, 2)
        )

        # Indicator (starts at center)
        indicator_width = 10
        self._pitch_bend_item = self.canvas.create_rectangle(
            x, y, x + track_width, y + track_height,
            fill="",
            outline="",
            width=0
        )
        self._pitch_bend_indicator = self.canvas.create_rectangle(
            center_x - indicator_width / 2, y + 2,
            center_x + indicator_width / 2, y + track_height - 2,
            fill=Colors.UNTESTED,
            outline=Colors.BORDER,
            width=1
        )

        # Labels
        self.canvas.create_text(
            x + track_width / 2, y - 12,
            text="PITCH BEND",
            fill=Colors.TEXT,
            font=("Helvetica", 9, "bold")
        )
        self.canvas.create_text(
            x - 10, y + track_height / 2,
            text="L",
            fill=Colors.TEXT,
            font=("Helvetica", 8)
        )
        self.canvas.create_text(
            x + track_width + 10, y + track_height / 2,
            text="R",
            fill=Colors.TEXT,
            font=("Helvetica", 8)
        )

    def update_cc_state(self, cc_num: int, tested: bool = False,
                        valid: bool = False, active: bool = False):
        """Update visual state of a CC component"""
        cc_num = int(cc_num)  # Ensure integer type

        if cc_num not in self._cc_items:
            return

        # Ensure state exists in dictionary
        if cc_num not in self._cc_states:
            self._cc_states[cc_num] = VisualState()

        state = self._cc_states[cc_num]
        state.tested = tested or state.tested
        state.valid = valid
        state.active = active

        color = self._get_state_color(state)
        self.canvas.itemconfig(self._cc_items[cc_num], fill=color)
        self.canvas.update_idletasks()  # Force canvas redraw

    def update_note_state(self, note: int, tested: bool = False,
                          valid: bool = False, active: bool = False):
        """Update visual state of a note"""
        if note not in self._note_items:
            return

        state = self._note_states.get(note, VisualState())
        state.tested = tested or state.tested
        state.valid = valid
        state.active = active

        # For notes, we need to preserve the key color when not active
        if active:
            color = Colors.ACTIVE
        elif tested:
            color = Colors.VALID if valid else Colors.INVALID
        else:
            # Determine if black or white key
            if note in [54, 56, 58, 61, 63, 66, 68, 70, 73, 75]:
                color = Colors.BLACK_KEY
            else:
                color = Colors.WHITE_KEY

        self.canvas.itemconfig(self._note_items[note], fill=color)

    def update_pitch_bend(self, value: int, tested: bool = False, valid: bool = False):
        """
        Update pitch bend visualization.

        Args:
            value: Pitch bend value (-8192 to 8191)
            tested: Whether pitch bend has been tested
            valid: Whether the test was valid
        """
        if not self._pitch_bend_indicator:
            return

        self._pitch_bend_state.tested = tested or self._pitch_bend_state.tested
        self._pitch_bend_state.valid = valid

        # Calculate indicator position
        # Map -8192..8191 to track width
        track_x = 570  # Match _create_pitch_bend x position
        track_width = 120
        indicator_width = 10

        # Normalize to 0-1 range
        normalized = (value + 8192) / 16383.0
        indicator_x = track_x + (track_width - indicator_width) * normalized

        # Update indicator position
        self.canvas.coords(
            self._pitch_bend_indicator,
            indicator_x, self.canvas.coords(self._pitch_bend_indicator)[1],
            indicator_x + indicator_width, self.canvas.coords(self._pitch_bend_indicator)[3]
        )

        # Update color
        color = self._get_state_color(self._pitch_bend_state)
        self.canvas.itemconfig(self._pitch_bend_indicator, fill=color)

    def _get_state_color(self, state: VisualState) -> str:
        """Get color for a visual state"""
        if state.active:
            return Colors.ACTIVE
        elif state.tested:
            return Colors.VALID if state.valid else Colors.INVALID
        else:
            return Colors.UNTESTED

    def flash_component(self, cc_num: Optional[int] = None,
                        note: Optional[int] = None,
                        is_pitch_bend: bool = False):
        """Briefly flash a component to indicate activity"""
        if cc_num is not None and cc_num in self._cc_items:
            item = self._cc_items[cc_num]
            original_color = self.canvas.itemcget(item, "fill")
            self.canvas.itemconfig(item, fill=Colors.ACTIVE)
            self.after(100, lambda: self.canvas.itemconfig(item, fill=original_color))

        elif note is not None and note in self._note_items:
            item = self._note_items[note]
            original_color = self.canvas.itemcget(item, "fill")
            self.canvas.itemconfig(item, fill=Colors.ACTIVE)
            self.after(100, lambda: self.canvas.itemconfig(item, fill=original_color))

        elif is_pitch_bend and self._pitch_bend_indicator:
            original_color = self.canvas.itemcget(self._pitch_bend_indicator, "fill")
            self.canvas.itemconfig(self._pitch_bend_indicator, fill=Colors.ACTIVE)
            self.after(100, lambda: self.canvas.itemconfig(
                self._pitch_bend_indicator, fill=original_color))

    def reset_all_states(self):
        """Reset all components to untested state"""
        for cc_num in self._cc_items:
            self._cc_states[cc_num] = VisualState()
            self.canvas.itemconfig(self._cc_items[cc_num], fill=Colors.UNTESTED)

        for note in self._note_items:
            self._note_states[note] = VisualState()
            # Reset to appropriate key color
            if note in [54, 56, 58, 61, 63, 66, 68, 70, 73, 75]:
                self.canvas.itemconfig(self._note_items[note], fill=Colors.BLACK_KEY)
            else:
                self.canvas.itemconfig(self._note_items[note], fill=Colors.WHITE_KEY)

        self._pitch_bend_state = VisualState()
        if self._pitch_bend_indicator:
            self.canvas.itemconfig(self._pitch_bend_indicator, fill=Colors.UNTESTED)
            # Reset position to center
            track_x = 570
            track_width = 120
            indicator_width = 10
            center_x = track_x + track_width / 2 - indicator_width / 2
            coords = self.canvas.coords(self._pitch_bend_indicator)
            self.canvas.coords(
                self._pitch_bend_indicator,
                center_x, coords[1],
                center_x + indicator_width, coords[3]
            )
