#!/usr/bin/env python3
"""
LMN-3 Hardware Testing Tool

A real-time MIDI testing tool that visualizes the LMN-3 board layout
and validates incoming MIDI messages against the firmware specification.

Usage:
    python main.py

Requirements:
    pip install mido python-rtmidi
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from datetime import datetime
import threading

from midi_handler import MidiHandler, MidiMessage, MidiMessageType
from test_runner import TestRunner, TestEvent, ValidationResult
from board_canvas import BoardCanvas, Colors
from firmware_spec import (
    MIDI_CHANNEL, get_encoder_ccs, COMPONENT_GROUPS, DUMMY,
    get_all_valid_notes
)


class LMN3Tester(tk.Tk):
    """Main application window for LMN-3 Hardware Testing Tool"""

    def __init__(self):
        super().__init__()

        self.title("LMN-3 Hardware Tester")
        self.configure(bg=Colors.BACKGROUND)

        # Set minimum window size
        self.minsize(850, 700)

        # Initialize components
        self.midi_handler = MidiHandler()
        self.test_runner = TestRunner()

        # Set up callbacks
        self.midi_handler.set_callback(self._on_midi_message)
        self.test_runner.set_event_callback(self._on_test_event)

        # Create UI
        self._create_widgets()

        # Start device polling
        self._poll_devices()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Style configuration
        style = ttk.Style()
        style.configure("TFrame", background=Colors.BACKGROUND)
        style.configure("TLabel", background=Colors.BACKGROUND, foreground=Colors.TEXT)
        style.configure("TButton", padding=5)

        # === Header Section ===
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # MIDI Device selector
        device_frame = ttk.Frame(header_frame)
        device_frame.pack(side=tk.LEFT)

        ttk.Label(device_frame, text="MIDI Device:").pack(side=tk.LEFT, padx=(0, 5))

        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(
            device_frame,
            textvariable=self.device_var,
            state="readonly",
            width=30
        )
        self.device_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_selected)

        # Refresh button
        self.refresh_btn = ttk.Button(
            device_frame,
            text="Refresh",
            command=self._refresh_devices
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 20))

        # Status indicator
        self.status_frame = ttk.Frame(header_frame)
        self.status_frame.pack(side=tk.LEFT)

        ttk.Label(self.status_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))

        self.status_indicator = tk.Canvas(
            self.status_frame,
            width=12, height=12,
            bg=Colors.BACKGROUND,
            highlightthickness=0
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 5))
        self.status_circle = self.status_indicator.create_oval(
            2, 2, 10, 10,
            fill=Colors.INVALID
        )

        self.status_label = ttk.Label(self.status_frame, text="Disconnected")
        self.status_label.pack(side=tk.LEFT)

        # Octave/Channel display
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side=tk.RIGHT)

        self.octave_label = ttk.Label(info_frame, text="Octave: 0")
        self.octave_label.pack(side=tk.LEFT, padx=10)

        self.channel_label = ttk.Label(info_frame, text=f"Channel: {MIDI_CHANNEL + 1}")
        self.channel_label.pack(side=tk.LEFT)

        # === Board Canvas ===
        self.board_canvas = BoardCanvas(main_frame)
        self.board_canvas.pack(fill=tk.BOTH, expand=True, pady=10)

        # === Bottom Section (Log + Status) ===
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        # Left: Test Log
        log_frame = ttk.LabelFrame(bottom_frame, text="Test Log")
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            width=50,
            height=10,
            bg="#1E1E1E",
            fg=Colors.TEXT,
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configure log tags for colors
        self.log_text.tag_configure("valid", foreground="#4CAF50")
        self.log_text.tag_configure("invalid", foreground="#F44336")
        self.log_text.tag_configure("warning", foreground="#FF9800")
        self.log_text.tag_configure("info", foreground="#666666")  # Faded gray for DUMMY etc

        # Right: Validation Status
        status_frame = ttk.LabelFrame(bottom_frame, text="Validation Status")
        status_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Component group indicators
        self.group_indicators = {}
        for group_name in COMPONENT_GROUPS.keys():
            group_frame = ttk.Frame(status_frame)
            group_frame.pack(fill=tk.X, padx=10, pady=3)

            ttk.Label(group_frame, text=f"{group_name}:", width=12, anchor=tk.W).pack(side=tk.LEFT)

            indicator_frame = ttk.Frame(group_frame)
            indicator_frame.pack(side=tk.LEFT)

            indicators = []
            for i in range(len(COMPONENT_GROUPS[group_name])):
                canvas = tk.Canvas(
                    indicator_frame,
                    width=12, height=12,
                    bg=Colors.BACKGROUND,
                    highlightthickness=0
                )
                canvas.pack(side=tk.LEFT, padx=1)
                circle = canvas.create_oval(2, 2, 10, 10, fill=Colors.UNTESTED, outline=Colors.BORDER)
                indicators.append((canvas, circle))

            self.group_indicators[group_name] = indicators

        # Notes indicator (simplified)
        notes_frame = ttk.Frame(status_frame)
        notes_frame.pack(fill=tk.X, padx=10, pady=3)
        ttk.Label(notes_frame, text="Notes:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.notes_progress = ttk.Label(notes_frame, text="0/24")
        self.notes_progress.pack(side=tk.LEFT)

        # Pitch bend indicator
        pb_frame = ttk.Frame(status_frame)
        pb_frame.pack(fill=tk.X, padx=10, pady=3)
        ttk.Label(pb_frame, text="Pitch Bend:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.pb_canvas = tk.Canvas(pb_frame, width=12, height=12, bg=Colors.BACKGROUND, highlightthickness=0)
        self.pb_canvas.pack(side=tk.LEFT)
        self.pb_indicator = self.pb_canvas.create_oval(2, 2, 10, 10, fill=Colors.UNTESTED, outline=Colors.BORDER)

        # === Footer (Coverage + Actions) ===
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))

        # Coverage stats
        self.coverage_label = ttk.Label(
            footer_frame,
            text="COVERAGE: 0/57 tested"
        )
        self.coverage_label.pack(side=tk.LEFT)

        self.errors_label = ttk.Label(
            footer_frame,
            text="ERRORS: 0"
        )
        self.errors_label.pack(side=tk.LEFT, padx=20)

        self.warnings_label = ttk.Label(
            footer_frame,
            text="WARNINGS: 0"
        )
        self.warnings_label.pack(side=tk.LEFT)

        # Action buttons
        button_frame = ttk.Frame(footer_frame)
        button_frame.pack(side=tk.RIGHT)

        self.export_btn = ttk.Button(
            button_frame,
            text="Export",
            command=self._export_report
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(
            button_frame,
            text="Clear",
            command=self._clear_tests
        )
        self.clear_btn.pack(side=tk.LEFT)

    def _refresh_devices(self):
        """Refresh the list of available MIDI devices"""
        devices = self.midi_handler.get_available_devices()
        self.device_combo["values"] = devices

        if devices:
            # Try to find a Teensy device
            teensy_device = next(
                (d for d in devices if "teensy" in d.lower()),
                devices[0]
            )
            self.device_var.set(teensy_device)
        else:
            self.device_var.set("")

    def _poll_devices(self):
        """Poll for device changes periodically"""
        current_devices = self.midi_handler.get_available_devices()
        combo_values = list(self.device_combo["values"])

        if current_devices != combo_values:
            self.device_combo["values"] = current_devices

            # If currently selected device disappeared, disconnect
            if self.device_var.get() and self.device_var.get() not in current_devices:
                self.midi_handler.disconnect()
                self._update_connection_status(False)
                self.device_var.set("")

            # Auto-select first device if none selected
            if not self.device_var.get() and current_devices:
                self.device_var.set(current_devices[0])

        # Poll again in 2 seconds
        self.after(2000, self._poll_devices)

    def _on_device_selected(self, event=None):
        """Handle device selection"""
        device = self.device_var.get()
        if not device:
            return

        if self.midi_handler.connect(device):
            self._update_connection_status(True)
            self._log_message(f"Connected to {device}", "info")
        else:
            self._update_connection_status(False)
            self._log_message(f"Failed to connect to {device}", "invalid")

    def _update_connection_status(self, connected: bool):
        """Update connection status indicator"""
        if connected:
            self.status_indicator.itemconfig(self.status_circle, fill=Colors.VALID)
            self.status_label.config(text="Connected")
        else:
            self.status_indicator.itemconfig(self.status_circle, fill=Colors.INVALID)
            self.status_label.config(text="Disconnected")

    def _on_midi_message(self, msg: MidiMessage):
        """Handle incoming MIDI message (called from MIDI thread)"""
        # Process in test runner (which will trigger _on_test_event callback)
        self.test_runner.process_message(msg)

    def _on_test_event(self, event: TestEvent):
        """Handle test event (called from MIDI thread, update UI via after())"""
        # Schedule UI update on main thread
        self.after(0, lambda: self._update_ui_for_event(event))

    def _update_ui_for_event(self, event: TestEvent):
        """Update UI elements based on test event (runs on main thread)"""
        # Log the event
        tag = {
            ValidationResult.VALID: "valid",
            ValidationResult.INVALID: "invalid",
            ValidationResult.WARNING: "warning",
            ValidationResult.INFO: "info",
            ValidationResult.UNKNOWN: "warning",
        }.get(event.result, "info")

        self._log_message(event.to_log_string(), tag)

        # Update visual board
        msg = event.message

        if msg.type == MidiMessageType.CONTROL_CHANGE:
            cc_num = msg.control
            if cc_num != DUMMY:
                is_valid = event.result == ValidationResult.VALID
                is_pressed = msg.value == 127

                # Flash and update state
                self.board_canvas.update_cc_state(
                    cc_num,
                    tested=True,
                    valid=is_valid,
                    active=is_pressed
                )

                # Update group indicator
                self._update_group_indicator(cc_num, is_valid)

        elif msg.type in (MidiMessageType.NOTE_ON, MidiMessageType.NOTE_OFF):
            note = msg.note
            is_valid = event.result == ValidationResult.VALID
            is_on = msg.type == MidiMessageType.NOTE_ON

            # Get base note (accounting for transposition)
            transposition = self.test_runner.get_current_transposition()
            base_note = note - transposition

            self.board_canvas.update_note_state(
                base_note,
                tested=True,
                valid=is_valid,
                active=is_on
            )

            # Update notes progress
            self._update_notes_progress()

        elif msg.type == MidiMessageType.PITCH_BEND:
            is_valid = event.result == ValidationResult.VALID
            self.board_canvas.update_pitch_bend(
                msg.pitch,
                tested=True,
                valid=is_valid
            )

            # Update pitch bend indicator
            color = Colors.VALID if is_valid else Colors.INVALID
            self.pb_canvas.itemconfig(self.pb_indicator, fill=color)

        # Update octave display
        octave = self.test_runner.get_current_octave()
        self.octave_label.config(text=f"Octave: {octave:+d}" if octave != 0 else "Octave: 0")

        # Update coverage stats
        self._update_coverage_display()

    def _update_group_indicator(self, cc_num: int, is_valid: bool):
        """Update the indicator for a component's group"""
        for group_name, cc_list in COMPONENT_GROUPS.items():
            if cc_num in cc_list:
                idx = cc_list.index(cc_num)
                if idx < len(self.group_indicators.get(group_name, [])):
                    canvas, circle = self.group_indicators[group_name][idx]
                    color = Colors.VALID if is_valid else Colors.INVALID
                    canvas.itemconfig(circle, fill=color)
                break

    def _update_notes_progress(self):
        """Update notes tested count"""
        stats = self.test_runner.get_coverage_stats()
        tested = stats["notes"]["tested"]
        total = stats["notes"]["total"]
        self.notes_progress.config(text=f"{tested}/{total}")

    def _update_coverage_display(self):
        """Update coverage statistics display"""
        stats = self.test_runner.get_coverage_stats()

        tested = stats["total_tested"]
        total = stats["total_components"]
        self.coverage_label.config(text=f"COVERAGE: {tested}/{total} tested")

        errors = stats["errors"]
        self.errors_label.config(
            text=f"ERRORS: {errors}",
            foreground=Colors.INVALID if errors > 0 else Colors.TEXT
        )

        warnings = stats["warnings"]
        self.warnings_label.config(
            text=f"WARNINGS: {warnings}",
            foreground=Colors.WARNING if warnings > 0 else Colors.TEXT
        )

    def _log_message(self, message: str, tag: str = "info"):
        """Add a message to the log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _export_report(self):
        """Export test report to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"lmn3_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if filename:
            try:
                report = self.test_runner.export_report()
                with open(filename, "w") as f:
                    f.write(report)
                self._log_message(f"Report exported to {filename}", "info")
                messagebox.showinfo("Export Successful", f"Report saved to:\n{filename}")
            except Exception as e:
                self._log_message(f"Export failed: {e}", "invalid")
                messagebox.showerror("Export Failed", str(e))

    def _clear_tests(self):
        """Clear all test state"""
        self.test_runner.clear()
        self.board_canvas.reset_all_states()

        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Reset indicators
        for group_name, indicators in self.group_indicators.items():
            for canvas, circle in indicators:
                canvas.itemconfig(circle, fill=Colors.UNTESTED)

        self.notes_progress.config(text="0/24")
        self.pb_canvas.itemconfig(self.pb_indicator, fill=Colors.UNTESTED)

        # Reset stats
        self._update_coverage_display()
        self.octave_label.config(text="Octave: 0")

        self._log_message("Tests cleared", "info")

    def _on_close(self):
        """Handle window close"""
        self.midi_handler.disconnect()
        self.destroy()


def main():
    """Main entry point"""
    app = LMN3Tester()
    app.mainloop()


if __name__ == "__main__":
    main()
