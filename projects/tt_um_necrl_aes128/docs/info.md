## How it works

AES-128 hardware encryption peripheral for a TinyQV RISC-V SoC. Composite-field S-box, 2-phase pipelined round, one-hot fault-detecting FSM, LFSR DPA countermeasure, FIPS-197 power-on self-test, and write-only key registers.

## How to test

See the pinout in `info.yaml`. This tile was imported from the signed-off
University of Arizona / AI-HDL collection and uses the standard Tiny Tapeout
clock, reset, and `ui`/`uo`/`uio` harness.

## Author

Team NeCRL (Parsa Mirfasihi, Waylon Woo, Ethan Weldon) - SFSU
