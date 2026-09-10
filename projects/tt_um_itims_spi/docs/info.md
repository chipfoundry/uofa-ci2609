## How it works

Secure full-duplex SPI master for the TinyQV RISC-V SoC. Supports all four SPI modes, 4-8 bit words, LSB/MSB-first, manual CS override and transfer-complete IRQ, plus a 32-bit tamper-evident hardware lock, an autonomous sleep-walker polling FSM with interval timers, and a serial CRC-16-CCITT engine.

## How to test

See the pinout in `info.yaml`. This tile was imported from the signed-off
University of Arizona / AI-HDL collection and uses the standard Tiny Tapeout
clock, reset, and `ui`/`uo`/`uio` harness.

## Author

Team ITIMS-Boys (HUST/ITIMS)
