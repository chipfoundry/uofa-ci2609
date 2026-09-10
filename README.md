[![verification](../../actions/workflows/verification.yaml/badge.svg)](../../actions/workflows/verification.yaml)
[![tt_datasheet](../../actions/workflows/tt_datasheet.yaml/badge.svg)](../../actions/workflows/tt_datasheet.yaml)
[![gds](../../actions/workflows/gds.yaml/badge.svg)](../../actions/workflows/gds.yaml)
[![precheck](../../actions/workflows/precheck.yaml/badge.svg)](../../actions/workflows/precheck.yaml)

# University of Arizona CI2609

Private Tiny Tapeout chip for the University of Arizona on the ChipFoundry [CI2609](https://platform.chipfoundry.io/status/ci2609) shuttle (SKY130 / openframe).

Designs are imported from the signed-off collection at [parsamrf/AI-HDL-Tape-out-Chipfoundry](https://github.com/parsamrf/AI-HDL-Tape-out-Chipfoundry).

To learn about the chip's architecture, see the [multiplexer documentation](https://github.com/TinyTapeout/tt-multiplexer/blob/main/docs/INFO.md). To rebuild, see [BUILDING.md](BUILDING.md).

## Tiny Tapeout tiles on this chip

| Macro | Tiles | Group |
| --- | --- | --- |
| `tt_um_chip_rom` | 1x1 | Tiny Tapeout ROM (shuttle id `ci2609`) |
| `tt_um_factory_test` | 1x1 | Tiny Tapeout factory test |
| `tt_um_uofa_traffic` | 1x1 | University of Arizona — smart traffic-light controller |
| `tt_um_itims_spi` | 2x2 | HUST/ITIMS — secure SPI master |
| `tt_um_necrl_aes128` | 4x2 | SFSU NeCRL — AES-128 peripheral |

## Designs that cannot sit on the Tiny Tapeout mux

The same collection also has eight standalone LibreLane SoCs. They are DRC/LVS clean, but they were not hardened to Tiny Tapeout tile size or pin locations, so they cannot be assembled on this mux chip:

| Design | Die | Why it does not fit |
| --- | --- | --- |
| `uofa-bmi-zane` | 0.49 × 0.50 mm | No `tt_um_*` wrapper; square die, not a TT tile |
| `uofa-bmu-palma` | 0.49 × 0.50 mm | Same |
| `uofa-vec-feng` | 0.40 × 0.41 mm | Same |
| `uofa-bp-rumsey` | 1.40 × 1.41 mm | Larger than the max TT tile (8x4 is 1.38 × 0.51 mm) |
| `uofa-gpio-gulvady` | 1.40 × 1.41 mm | Same |
| `uofa-mul-colincore` | 1.39 × 1.40 mm | Same |
| `uofa-vec-chakravarthy` | 1.42 × 1.43 mm | Same |
| `slm-soc` | 2.58 × 2.59 mm | Same |

Those SoCs would need a separate openframe/Caravel slot, or a re-harden into TT tiles, before they can tape out on this architecture.

## Required macros

`projects.txt` must include:

- `https://github.com/TinyTapeout/tt-chip-rom`
- `https://github.com/TinyTapeout/ttsky26c-factory-test`
