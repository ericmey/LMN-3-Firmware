"""
Test Runner for LMN-3 Tester

Manages test state, validates MIDI messages against firmware spec,
and generates test reports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Callable
import json

from firmware_spec import (
    MIDI_CHANNEL, DUMMY, CC_COMPONENTS, ComponentType, ComponentSpec,
    get_all_valid_cc_numbers, get_all_valid_notes, get_encoder_ccs,
    is_valid_encoder_value, is_valid_button_value, is_valid_octave_value,
    get_component_name, COMPONENT_GROUPS, OCTAVE_CHANGE,
    MIN_NOTE, MAX_NOTE, TRANSPOSITION_RANGE
)
from midi_handler import MidiMessage, MidiMessageType


class ValidationResult(Enum):
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"  # For non-standard but expected behavior
    INFO = "info"  # For informational messages like DUMMY
    UNKNOWN = "unknown"


@dataclass
class TestEvent:
    """Record of a single test event"""
    timestamp: datetime
    message: MidiMessage
    result: ValidationResult
    component_name: str
    details: str = ""

    def to_log_string(self) -> str:
        """Format as log string for display"""
        time_str = self.timestamp.strftime("%H:%M:%S")
        icon = {
            ValidationResult.VALID: "\u2713",  # checkmark
            ValidationResult.INVALID: "\u2717",  # X
            ValidationResult.WARNING: "\u26a0",  # warning
            ValidationResult.INFO: "\u2022",  # bullet
            ValidationResult.UNKNOWN: "?",
        }[self.result]
        return f"{time_str} {self.message} {icon} {self.result.value.upper()}"


@dataclass
class ComponentTestState:
    """Test state for a single component"""
    tested: bool = False
    valid: bool = False
    test_count: int = 0
    last_value: Optional[int] = None
    last_test_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)


class TestRunner:
    """
    Manages test state and validates incoming MIDI messages.

    Tracks which components have been tested, validates messages
    against the firmware specification, and generates reports.
    """

    def __init__(self):
        # CC component states (keyed by CC number)
        self._cc_states: Dict[int, ComponentTestState] = {}
        # Note states (keyed by note number)
        self._note_states: Dict[int, ComponentTestState] = {}
        # Pitch bend state
        self._pitch_bend_state = ComponentTestState()
        # Event log
        self._events: List[TestEvent] = []
        # Current transposition (updated when OCTAVE_CHANGE received)
        self._current_transposition: int = 0
        # Callback for UI updates
        self._on_event_callback: Optional[Callable[[TestEvent], None]] = None
        # Error count
        self._error_count: int = 0
        # Warning count (DUMMY messages)
        self._warning_count: int = 0

        self._initialize_states()

    def _initialize_states(self):
        """Initialize test states for all components"""
        # Initialize CC states
        for cc_num in get_all_valid_cc_numbers():
            self._cc_states[cc_num] = ComponentTestState()

        # Initialize note states
        for note in get_all_valid_notes():
            self._note_states[note] = ComponentTestState()

        # Pitch bend already initialized

    def set_event_callback(self, callback: Callable[[TestEvent], None]):
        """Set callback for when events are processed"""
        self._on_event_callback = callback

    def process_message(self, msg: MidiMessage) -> TestEvent:
        """
        Process and validate an incoming MIDI message.

        Args:
            msg: The MIDI message to process

        Returns:
            TestEvent with validation result
        """
        now = datetime.now()

        # Check channel first
        if msg.channel != MIDI_CHANNEL:
            event = TestEvent(
                timestamp=now,
                message=msg,
                result=ValidationResult.INVALID,
                component_name="CHANNEL",
                details=f"Expected channel {MIDI_CHANNEL + 1}, got {msg.channel + 1}"
            )
            self._error_count += 1
            self._events.append(event)
            if self._on_event_callback:
                self._on_event_callback(event)
            return event

        # Route to appropriate handler
        if msg.type == MidiMessageType.CONTROL_CHANGE:
            event = self._process_cc(msg, now)
        elif msg.type in (MidiMessageType.NOTE_ON, MidiMessageType.NOTE_OFF):
            event = self._process_note(msg, now)
        elif msg.type == MidiMessageType.PITCH_BEND:
            event = self._process_pitch_bend(msg, now)
        else:
            event = TestEvent(
                timestamp=now,
                message=msg,
                result=ValidationResult.UNKNOWN,
                component_name="UNKNOWN",
                details=f"Unexpected message type: {msg.type}"
            )
            self._error_count += 1

        self._events.append(event)
        if self._on_event_callback:
            self._on_event_callback(event)
        return event

    def _process_cc(self, msg: MidiMessage, now: datetime) -> TestEvent:
        """Process a Control Change message"""
        cc_num = msg.control
        value = msg.value

        # Check for DUMMY
        if cc_num == DUMMY:
            return TestEvent(
                timestamp=now,
                message=msg,
                result=ValidationResult.INFO,
                component_name="DUMMY",
                details="Disabled position"
            )

        # Get component spec
        spec = CC_COMPONENTS.get(cc_num)
        if not spec:
            self._error_count += 1
            return TestEvent(
                timestamp=now,
                message=msg,
                result=ValidationResult.INVALID,
                component_name=f"CC#{cc_num}",
                details=f"Unknown CC number: {cc_num}"
            )

        # Validate value based on component type
        valid = True
        details = ""

        if spec.component_type == ComponentType.ENCODER_ROTATION:
            if not is_valid_encoder_value(value):
                valid = False
                details = f"Expected 1 (CW) or 127 (CCW), got {value}"
            else:
                details = "CW" if value == 1 else "CCW"

        elif spec.component_type == ComponentType.ENCODER_BUTTON:
            if not is_valid_button_value(value):
                valid = False
                details = f"Expected 0 or 127, got {value}"
            else:
                details = "pressed" if value == 127 else "released"

        elif spec.component_type in (ComponentType.TRANSPORT_BUTTON,
                                      ComponentType.EDIT_BUTTON):
            if not is_valid_button_value(value):
                valid = False
                details = f"Expected 0 or 127, got {value}"
            else:
                details = "pressed" if value == 127 else "released"

        elif spec.component_type == ComponentType.SPECIAL_CONTROL:
            if cc_num == OCTAVE_CHANGE:
                if not is_valid_octave_value(value):
                    valid = False
                    details = f"Expected 0-8, got {value}"
                else:
                    # Update current transposition
                    self._current_transposition = (value - 4) * 12  # 0-8 maps to -4 to +4 octaves
                    octave_display = value - 4
                    details = f"octave={octave_display:+d} (transpose={self._current_transposition:+d} semitones)"
            else:
                # PLUS/MINUS buttons
                if not is_valid_button_value(value):
                    valid = False
                    details = f"Expected 0 or 127, got {value}"
                else:
                    details = "pressed" if value == 127 else "released"

        # Update state
        state = self._cc_states.get(cc_num)
        if state:
            state.tested = True
            state.valid = valid
            state.test_count += 1
            state.last_value = value
            state.last_test_time = now
            if not valid:
                state.errors.append(details)

        result = ValidationResult.VALID if valid else ValidationResult.INVALID
        if not valid:
            self._error_count += 1

        return TestEvent(
            timestamp=now,
            message=msg,
            result=result,
            component_name=spec.name,
            details=details
        )

    def _process_note(self, msg: MidiMessage, now: datetime) -> TestEvent:
        """Process a Note On/Off message"""
        note = msg.note
        is_note_on = msg.type == MidiMessageType.NOTE_ON

        # Check if note is in valid range (considering transposition)
        valid_notes = get_all_valid_notes()

        # Check base note (without transposition)
        base_note = note - self._current_transposition
        if base_note in valid_notes:
            # Valid note considering current transposition
            state = self._note_states.get(base_note)
            if state:
                state.tested = True
                state.valid = True
                state.test_count += 1
                state.last_value = 127 if is_note_on else 0
                state.last_test_time = now

            details = "ON" if is_note_on else "OFF"
            if self._current_transposition != 0:
                details += f" (base={base_note}, transpose={self._current_transposition:+d})"

            return TestEvent(
                timestamp=now,
                message=msg,
                result=ValidationResult.VALID,
                component_name=f"Note {note}",
                details=details
            )

        # Check if note could be valid with different transposition
        # (valid base note range is 53-76, transposition is ±48 semitones)
        could_be_valid = False
        for base in valid_notes:
            if base - TRANSPOSITION_RANGE <= note <= base + TRANSPOSITION_RANGE:
                could_be_valid = True
                break

        if could_be_valid:
            # Might be valid but with unexpected transposition
            self._warning_count += 1
            return TestEvent(
                timestamp=now,
                message=msg,
                result=ValidationResult.WARNING,
                component_name=f"Note {note}",
                details=f"Unexpected transposition? Current={self._current_transposition:+d}"
            )
        else:
            self._error_count += 1
            return TestEvent(
                timestamp=now,
                message=msg,
                result=ValidationResult.INVALID,
                component_name=f"Note {note}",
                details=f"Note outside valid range (53-76 ± transposition)"
            )

    def _process_pitch_bend(self, msg: MidiMessage, now: datetime) -> TestEvent:
        """Process a Pitch Bend message"""
        pitch = msg.pitch  # -8192 to 8191 in mido

        # Update state
        self._pitch_bend_state.tested = True
        self._pitch_bend_state.valid = True
        self._pitch_bend_state.test_count += 1
        self._pitch_bend_state.last_value = pitch
        self._pitch_bend_state.last_test_time = now

        # Determine position description
        if abs(pitch) < 100:
            position = "center"
        elif pitch > 0:
            position = "right"
        else:
            position = "left"

        return TestEvent(
            timestamp=now,
            message=msg,
            result=ValidationResult.VALID,
            component_name="PITCH_BEND",
            details=f"{position} ({pitch})"
        )

    def get_cc_state(self, cc_num: int) -> Optional[ComponentTestState]:
        """Get test state for a CC component"""
        return self._cc_states.get(cc_num)

    def get_note_state(self, note: int) -> Optional[ComponentTestState]:
        """Get test state for a note"""
        return self._note_states.get(note)

    def get_pitch_bend_state(self) -> ComponentTestState:
        """Get test state for pitch bend"""
        return self._pitch_bend_state

    def get_coverage_stats(self) -> Dict:
        """
        Get test coverage statistics.

        Returns:
            Dict with tested/total counts for each category
        """
        # CC components by group
        stats = {
            "groups": {},
            "notes": {
                "tested": sum(1 for s in self._note_states.values() if s.tested),
                "total": len(self._note_states),
                "valid": sum(1 for s in self._note_states.values() if s.tested and s.valid),
            },
            "pitch_bend": {
                "tested": self._pitch_bend_state.tested,
                "valid": self._pitch_bend_state.valid,
            },
            "total_tested": 0,
            "total_components": 0,
            "errors": self._error_count,
            "warnings": self._warning_count,
        }

        # Calculate group stats
        for group_name, cc_list in COMPONENT_GROUPS.items():
            tested = sum(1 for cc in cc_list
                        if cc in self._cc_states and self._cc_states[cc].tested)
            valid = sum(1 for cc in cc_list
                       if cc in self._cc_states and self._cc_states[cc].tested
                       and self._cc_states[cc].valid)
            stats["groups"][group_name] = {
                "tested": tested,
                "total": len(cc_list),
                "valid": valid,
            }

        # Calculate totals
        total_cc_tested = sum(1 for s in self._cc_states.values() if s.tested)
        total_cc = len(self._cc_states)
        total_notes_tested = stats["notes"]["tested"]
        total_notes = stats["notes"]["total"]
        pitch_tested = 1 if stats["pitch_bend"]["tested"] else 0

        stats["total_tested"] = total_cc_tested + total_notes_tested + pitch_tested
        stats["total_components"] = total_cc + total_notes + 1  # +1 for pitch bend

        return stats

    def get_events(self, limit: int = 100) -> List[TestEvent]:
        """Get recent test events"""
        return self._events[-limit:]

    def clear(self):
        """Clear all test state and history"""
        self._events.clear()
        self._error_count = 0
        self._warning_count = 0
        self._current_transposition = 0
        self._pitch_bend_state = ComponentTestState()
        self._initialize_states()

    def get_current_transposition(self) -> int:
        """Get current transposition in semitones"""
        return self._current_transposition

    def get_current_octave(self) -> int:
        """Get current octave offset (-4 to +4)"""
        return self._current_transposition // 12

    def export_report(self) -> str:
        """Generate a test report as JSON string"""
        stats = self.get_coverage_stats()

        report = {
            "timestamp": datetime.now().isoformat(),
            "coverage": stats,
            "events": [
                {
                    "time": e.timestamp.isoformat(),
                    "component": e.component_name,
                    "result": e.result.value,
                    "details": e.details,
                    "message": str(e.message),
                }
                for e in self._events
            ],
            "untested_components": {
                "cc": [
                    get_component_name(cc)
                    for cc, state in self._cc_states.items()
                    if not state.tested
                ],
                "notes": [
                    note for note, state in self._note_states.items()
                    if not state.tested
                ],
                "pitch_bend": not self._pitch_bend_state.tested,
            },
        }

        return json.dumps(report, indent=2)

    def get_group_states(self, group_name: str) -> List[ComponentTestState]:
        """Get test states for a component group"""
        if group_name not in COMPONENT_GROUPS:
            return []
        return [
            self._cc_states.get(cc, ComponentTestState())
            for cc in COMPONENT_GROUPS[group_name]
        ]
