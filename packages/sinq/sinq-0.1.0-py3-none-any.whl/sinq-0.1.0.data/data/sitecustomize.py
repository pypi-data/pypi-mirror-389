# sitecustomize.py
import os, sys
if str(os.getenv("SINQ_AUTO_PATCH","1")).lower() not in ("0","false","no","off",""):
    try:
        from sinq.hf_io import patch_hf_pretrained_io
        patch_hf_pretrained_io()
    except Exception as e:
        sys.stderr.write(f"[SINQ] sitecustomize autopatch failed: {e}\n")