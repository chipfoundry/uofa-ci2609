# Convert GDS to OAS for the Tiny Tapeout density-fix step.
# klayout -b -r gds_to_oas.py -rd gds=... -rd oas=...
import pya

layout = pya.Layout()
layout.read(gds)
layout.write(oas)
print(f"Wrote {oas}")
