## How it works

WiFi-assisted (ESP32-over-SPI) smart traffic-light controller for the TinyQV RISC-V SoC. Counts vehicles, applies congestion-aware thresholding, falls back to an inductive-loop detector, raises a level-triggered interrupt, and authenticates SPI packets with a keyed CRC8 and replay protection.

## How to test

See the pinout in `info.yaml`. This tile was imported from the signed-off
University of Arizona / AI-HDL collection and uses the standard Tiny Tapeout
clock, reset, and `ui`/`uo`/`uio` harness.

## Author

Team Maestros (University of Arizona)
