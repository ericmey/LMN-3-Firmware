# RP2040 Carrier Board Pin Mapping

This document defines the pin mapping for an RP2040 carrier board designed to be footprint-compatible with the Teensy 4.1, allowing the same main PCB to accept either microcontroller.

## Overview

| Microcontroller | GPIO Pins | ADC Channels | Price |
|-----------------|-----------|--------------|-------|
| Teensy 4.1      | 55        | 18           | ~$35  |
| RP2040 (Pico)   | 30        | 4            | ~$4   |

The LMN-3 firmware uses **28 pins** total, which fits within the RP2040's 30 GPIO pins.

## Pin Mapping Table

### Matrix Row Pins

| Function | Teensy 4.1 Pin | RP2040 Pin | Notes |
|----------|----------------|------------|-------|
| ROW_0    | 24             | GP0        | Digital I/O |
| ROW_1    | 23             | GP1        | Digital I/O |
| ROW_2    | 34             | GP2        | Digital I/O |
| ROW_3    | 35             | GP3        | Digital I/O |
| ROW_4    | 28             | GP4        | Digital I/O |

### Matrix Column Pins

| Function | Teensy 4.1 Pin | RP2040 Pin | Notes |
|----------|----------------|------------|-------|
| COL_0    | 9              | GP5        | Digital I/O |
| COL_1    | 8              | GP6        | Digital I/O |
| COL_2    | 7              | GP7        | Digital I/O |
| COL_3    | 4              | GP8        | Digital I/O |
| COL_4    | 3              | GP9        | Digital I/O |
| COL_5    | 2              | GP10       | Digital I/O |
| COL_6    | 1              | GP11       | Digital I/O |
| COL_7    | 0              | GP12       | Digital I/O |
| COL_8    | 25             | GP13       | Digital I/O |
| COL_9    | 14             | GP14       | Digital I/O |
| COL_10   | 13             | GP15       | Digital I/O |
| COL_11   | 41             | GP16       | Digital I/O |
| COL_12   | 40             | GP17       | Digital I/O |
| COL_13   | 36             | GP18       | Digital I/O |

### Rotary Encoder Pins

| Function   | Teensy 4.1 Pins | RP2040 Pins   | Notes |
|------------|-----------------|---------------|-------|
| Encoder 1  | 5, 6            | GP19, GP20    | Quadrature A/B |
| Encoder 2  | 26, 27          | GP21, GP22    | Quadrature A/B |
| Encoder 3  | 29, 30          | GP23, GP24    | Quadrature A/B |
| Encoder 4  | 31, 32          | GP25, GP27    | Quadrature A/B (skip GP26 for ADC) |

### Analog Input

| Function    | Teensy 4.1 Pin | RP2040 Pin | Notes |
|-------------|----------------|------------|-------|
| Pitch Bend  | A15            | GP26       | ADC0 - 12-bit resolution |

## RP2040 Pin Usage Summary

```
Used:     GP0-GP27 (28 pins)
Spare:    GP28, GP29 (both ADC-capable)
Reserved: USB (internal), BOOTSEL
```

## Carrier Board Design Notes

1. **Form Factor**: The carrier board should match the Teensy 4.1 outer dimensions and pin header positions.

2. **Pin Header Mapping**: Route RP2040 GPIO to the corresponding Teensy header positions per the mapping above.

3. **Power**:
   - Teensy 4.1 runs at 3.3V logic (same as RP2040)
   - Provide 3.3V regulation from 5V USB or VIN

4. **USB**: Route RP2040 USB D+/D- to USB connector (or use Pico's onboard USB)

5. **Reset/Boot**: Consider exposing BOOTSEL button for firmware updates

6. **Mounting**: Standard Pico can be soldered directly or use castellated edges

## Firmware Changes Required

When porting to RP2040, update `src/config.h`:

```cpp
#pragma once

// RP2040 Pin Configuration
const int HORIZONTAL_PB_PIN = 26;  // GP26 (ADC0)

// Row Pins
const int ROW_0 = 0;
const int ROW_1 = 1;
const int ROW_2 = 2;
const int ROW_3 = 3;
const int ROW_4 = 4;

// Col Pins
const int COL_0 = 5;
const int COL_1 = 6;
const int COL_2 = 7;
const int COL_3 = 8;
const int COL_4 = 9;
const int COL_5 = 10;
const int COL_6 = 11;
const int COL_7 = 12;
const int COL_8 = 13;
const int COL_9 = 14;
const int COL_10 = 15;
const int COL_11 = 16;
const int COL_12 = 17;
const int COL_13 = 18;
```

## RP2040 Platform Options

| Board | Form Factor | Price | Notes |
|-------|-------------|-------|-------|
| Raspberry Pi Pico | 51mm x 21mm | ~$4 | Standard, castellated edges |
| RP2040-Zero | 23.5mm x 18mm | ~$5 | Tiny, good for carrier boards |
| Seeed XIAO RP2040 | 21mm x 17.5mm | ~$6 | Very small, USB-C |
| Waveshare RP2040-Plus | 51mm x 21mm | ~$8 | Pico-compatible, more flash |

## References

- [RP2040 Datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
- [Teensy 4.1 Pinout](https://www.pjrc.com/store/teensy41.html)
- [Arduino-Pico Core](https://github.com/earlephilhower/arduino-pico)
- [TinyUSB MIDI](https://github.com/hathach/tinyusb)
