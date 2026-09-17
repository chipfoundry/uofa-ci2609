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
| `tt_um_vec_coproc` | 4x2 | UofA — PicoRV32 SIMD vector coprocessor |
| `tt_um_bmi_soc` | 6x2 | UofA — BMI SoC |
| `tt_um_bmu_soc` | 6x2 | UofA — BMU SoC |
| `tt_um_mul_soc` | 8x2 | UofA — multiplier SoC |
| `tt_um_gpio_soc` | 8x2 | UofA — GPIO SoC |
| `tt_um_bp_soc` | 8x2 | UofA — branch predictor SoC |
| `tt_um_vec_proc` | 8x2 | UofA — vector processor |
| `tt_um_slm_dma` | 6x2 | SLM DMA engine |
| `tt_um_slm_kv` | 6x2 | SLM KV-cache controller |
| `tt_um_slm_softmax` | 8x2 | SLM softmax accelerator |
| `tt_um_slm_cpu` | 8x2 | SLM RV32IM CPU |
| `tt_um_slm_rmsnorm` | 8x2 | SLM RMSNorm accelerator |
| `tt_um_slm_gemm` | 8x4 | SLM INT8 8×8 systolic GEMM (huge_modules mux 21) |

## Designs not on this mux

- The original standalone SoC GDS from the collection still does not match TT pinout; the rows above are the re-hardened TT wrappers.

## Required macros

`projects.txt` must include:

- `https://github.com/TinyTapeout/tt-chip-rom`
- `https://github.com/TinyTapeout/ttsky26c-factory-test`
