#!/bin/bash
set -u
cd "$(dirname "$0")/.."
ROOT="$PWD"
RYU="${RYU:-$ROOT/venv39/bin/ryu-manager}"
OUT="${OUT:-runs_rev}"
mkdir -p "$OUT"
CAP=${CAP:-100}
ADVN=${ADVN:-85}
FLOWS=${FLOWS:-60}
DUR=${DUR:-60}
SEEDS=${SEEDS:-10}
K=${K:-3}
COUNT=${COUNT:-poll}
POLICIES=${POLICIES:-"sp ecmp urm larm greedy sp_retry larm_retry"}
for s in $(seq 1 "$SEEDS"); do
  for pol in $POLICIES; do
    out="$OUT/atk_${pol}_s${s}.json"
    [ -s "$out" ] && continue
    echo "== attack run: policy=$pol seed=$s =="
    mn -c >/dev/null 2>&1
    timeout 200 env LARM_ROOT="$ROOT" RYU="$RYU" python3 testbed/net.py \
      --topo fattree4 --policy "$pol" --seed "$s" --cap "$CAP" \
      --adv_n "$ADVN" --k "$K" --count "$COUNT" --attack --flows "$FLOWS" --dur "$DUR" --out "$out" \
      2>"$OUT/atk_${pol}_s${s}.err" | tail -1
    sleep 3
  done
done
echo "ATTACK_REV_DONE"
