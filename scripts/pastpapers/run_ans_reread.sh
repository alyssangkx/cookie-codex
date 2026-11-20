#!/bin/bash
# DRAFT, not started. Two independent VL-32B reads of the answer-key pages found by `anskey_ocr.py find-answer-pages`.
# Before: copy the dev folder anskey/reread/pages-*.jsonl and code/scripts/pastpapers/ans_reread.py to the server, and make
# sure the pages (pastpapers_full/<subject>/<year>/pages/pNNNN.jpg) are there. After: copy */*/ansreread/ back to dev's
# pastpapers/<subject>/<year>/, then `load_pp.py select --reread-keys` (blind check on the new keys still applies).
# Waits for the GPUs like the other queues (never runs while wy_alg_server is active). Log: vlm/ansreread.log.
cd /data/alvin/cookie
export HF_HUB_CACHE=/data/alvin/hub VLLM_USE_V1=0 PP_EAGER=1 PP_ROOT=/data/alvin/cookie/pastpapers_full PP_TP=2
PY=/data/alvin/envs/ppvlm/bin/python
msg() { echo "$(date "+%F %T") $*" >> vlm/ansreread-done.txt; echo "$*"; }
[ "$(systemctl is-active wy_alg_server)" = active ] && { msg "STOP: wy_alg_server active"; exit 2; }
args=(); for f in anskey/reread/pages-*.jsonl; do args+=(--pages "$f"); done
$PY code/scripts/pastpapers/ans_reread.py "${args[@]}" >> vlm/ansreread.log 2>&1 && msg "ansreread done: $(ls pastpapers_full/*/*/ansreread/p*.json 2>/dev/null | wc -l) pages" || msg "STOP: ansreread crashed"
