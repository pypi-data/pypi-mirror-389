# sinq/_autopatch.py
import os, sys
def run():
    if str(os.getenv("SINQ_AUTO_PATCH","1")).lower() in ("0","false","no","off",""):
        return
    try:
        from .hf_io import patch_hf_pretrained_io
        patch_hf_pretrained_io()
    except Exception as e:
        # don't crash startup; make failures visible
        sys.stderr.write(f"[SINQ] autopatch failed: {e}\n")
