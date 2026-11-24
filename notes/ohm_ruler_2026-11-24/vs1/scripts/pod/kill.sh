#!/bin/bash
pkill -f "runO[.]sh"; pkill -f "xargs -P"; pkill -f "vs_dry_noise[.]py"; pkill -f "ohm_ruler_night[.]py"; sleep 2
rm -rf /root/work /root/out /root/progress.txt; mkdir -p /root/work /root/out
echo killed
