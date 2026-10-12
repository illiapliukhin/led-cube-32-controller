#!/bin/bash
cd /workspace/.kicad10/AppDir && export PYTHONPATH=/workspace/.py311site; exec ./AppRun python3.11 "$@"
