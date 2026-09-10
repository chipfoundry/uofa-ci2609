# sky130_tt_sc_hd\_\_newfill_3.gds

A drop-in replacement for `sky130_fd_sc_hd__decap_3` that removes all poly
gate structures, reducing poly density without changing the cell footprint.

Used by [replace_decap.py](replace_decap.py) to fix poly density DRC violations (`cpoly.pd.1e`).

## How it was created

Source cell: `sky130_fd_sc_hd__decap_3` from the SKY130 PDK

- PDK version: `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`

The following layers were removed from `decap_3`:

- **poly.drawing (66/20)**: the poly gates (reduces poly density), 2 shapes
- **npc.drawing (95/20)**
- **text.drawing (83/44)**: text label saying "decap_3"

Two **licon1.drawing (66/44)** contacts that sat on top of the poly gates were also removed.
The remaining 6 contacts are in the diff/tap regions and are still valid.
