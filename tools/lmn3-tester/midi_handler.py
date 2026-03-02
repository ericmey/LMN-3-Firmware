"""
MIDI Handler for LMN-3 Tester

Handles MIDI input/output using mido + python-rtmidi.
Provides device enumeration, selection, and callback-based message handling.
"""

import threading
import queue
from typing import Callable, Optional, List
from dataclasses import dataclass
from enum import Enum

import mido


class MidiMessageType(Enum):
    NOTE_ON = "note_on"
    NOTE_OFF = "note_off"
    CONTROL_CHANGE = "control_change"
    PITCH_BEND = "pitchwheel"
    UNKNOWN = "unknown"


@dataclass
class MidiMessage:
    """Parsed MIDI message with metadata"""
    type: MidiMessageType
    channel: int
    note: Optional[int] = None
    velocity: Optional[int] = None
    control: Optional[int] = None
    value: Optional[int] = None
    pitch: Optional[int] = None
    raw: Optional[mido.Message] = None

    def __str__(self) -> str:
        if self.type == MidiMessageType.NOTE_ON:
            return f"Note {self.note} ON vel={self.velocity} ch{self.channel + 1}"
        elif self.type == MidiMessageType.NOTE_OFF:
            return f"Note {self.note} OFF ch{self.channel + 1}"
        elif self.type == MidiMessageType.CONTROL_CHANGE:
            return f"CC#{self.control}={self.value} ch{self.channel + 1}"
        elif self.type == MidiMessageType.PITCH_BEND:
            return f"Pitch {self.pitch} ch{self.channel + 1}"
        else:
            return f"Unknown: {self.raw}"


class MidiHandler:
    """
    Thread-safe MIDI input handler with device selection.

    Usage:
        handler = MidiHandler()
        devices = handler.get_available_devices()
        handler.connect(devices[0])
        handler.set_callback(my_callback_function)
        # ... later
        handler.disconnect()
    """

    def __init__(self):
        self._port: Optional[mido.ports.BaseInput] = None
        self._callback: Optional[Callable[[MidiMessage], None]] = None
        self._message_queue: queue.Queue = queue.Queue()
        self._running = False
        self._listener_thread: Optional[threading.Thread] = None
        self._connected_device: Optional[str] = None

    @staticmethod
    def get_available_devices() -> List[str]:
        """Return list of available MIDI input device names"""
        try:
            return mido.get_input_names()
        except Exception as e:
            print(f"Error getting MIDI devices: {e}")
            return []

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to a MIDI device"""
        return self._port is not None and self._running

    @property
    def connected_device(self) -> Optional[str]:
        """Get name of currently connected device"""
        return self._connected_device if self.is_connected else None

    def connect(self, device_name: str) -> bool:
        """
        Connect to a MIDI input device by name.

        Args:
            device_name: Name of the MIDI device to connect to

        Returns:
            True if connection successful, False otherwise
        """
        # Disconnect if already connected
        if self.is_connected:
            self.disconnect()

        try:
            self._port = mido.open_input(device_name)
            self._connected_device = device_name
            self._running = True
            self._listener_thread = threading.Thread(
                target=self._listen_loop,
                daemon=True
            )
            self._listener_thread.start()
            return True
        except Exception as e:
            print(f"Error connecting to {device_name}: {e}")
            self._port = None
            self._connected_device = None
            return False

    def disconnect(self):
        """Disconnect from current MIDI device"""
        self._running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=1.0)
            self._listener_thread = None
        if self._port:
            try:
                self._port.close()
            except Exception:
                pass
            self._port = None
        self._connected_device = None

    def set_callback(self, callback: Callable[[MidiMessage], None]):
        """
        Set callback function for incoming MIDI messages.

        The callback will be invoked from the listener thread,
        so it should be thread-safe if accessing shared state.

        Args:
            callback: Function that takes a MidiMessage argument
        """
        self._callback = callback

    def _listen_loop(self):
        """Internal listener loop running in separate thread"""
        while self._running and self._port:
            try:
                # Use iter_pending() for non-blocking reads
                for msg in self._port.iter_pending():
                    parsed = self._parse_message(msg)
                    if parsed and self._callback:
                        self._callback(parsed)
                # Small sleep to prevent busy-waiting
                threading.Event().wait(0.001)
            except Exception as e:
                if self._running:
                    print(f"Error in MIDI listener: {e}")

    def _parse_message(self, msg: mido.Message) -> Optional[MidiMessage]:
        """Parse a mido message into our MidiMessage format"""
        try:
            if msg.type == 'note_on':
                return MidiMessage(
                    type=MidiMessageType.NOTE_ON if msg.velocity > 0 else MidiMessageType.NOTE_OFF,
                    channel=msg.channel,
                    note=msg.note,
                    velocity=msg.velocity,
                    raw=msg
                )
            elif msg.type == 'note_off':
                return MidiMessage(
                    type=MidiMessageType.NOTE_OFF,
                    channel=msg.channel,
                    note=msg.note,
                    velocity=msg.velocity,
                    raw=msg
                )
            elif msg.type == 'control_change':
                return MidiMessage(
                    type=MidiMessageType.CONTROL_CHANGE,
                    channel=msg.channel,
                    control=msg.control,
                    value=msg.value,
                    raw=msg
                )
            elif msg.type == 'pitchwheel':
                return MidiMessage(
                    type=MidiMessageType.PITCH_BEND,
                    channel=msg.channel,
                    pitch=msg.pitch,
                    raw=msg
                )
            else:
                return MidiMessage(
                    type=MidiMessageType.UNKNOWN,
                    channel=getattr(msg, 'channel', 0),
                    raw=msg
                )
        except Exception as e:
            print(f"Error parsing MIDI message: {e}")
            return None

    def poll_messages(self) -> List[MidiMessage]:
        """
        Poll for any queued messages (alternative to callback).

        Returns:
            List of MidiMessage objects received since last poll
        """
        messages = []
        while True:
            try:
                msg = self._message_queue.get_nowait()
                messages.append(msg)
            except queue.Empty:
                break
        return messages

    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


def test_midi_handler():
    """Simple test function to verify MIDI handling"""
    handler = MidiHandler()

    print("Available MIDI devices:")
    devices = handler.get_available_devices()
    for i, device in enumerate(devices):
        print(f"  {i}: {device}")

    if not devices:
        print("No MIDI devices found!")
        return

    # Try to connect to first device
    print(f"\nConnecting to: {devices[0]}")
    if handler.connect(devices[0]):
        print("Connected! Listening for MIDI messages (Ctrl+C to stop)...")

        def print_message(msg: MidiMessage):
            print(f"  Received: {msg}")

        handler.set_callback(print_message)

        try:
            import time
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping...")
    else:
        print("Failed to connect!")

    handler.disconnect()
    print("Done.")


if __name__ == "__main__":
    test_midi_handler()
