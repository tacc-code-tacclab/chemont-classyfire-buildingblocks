#!/usr/bin/env bash
# Parallel segmented download of the ChEMBL 37 SQLite dump (EBI throttles per-connection,
# so N parallel byte-range streams multiply throughput). Verifies each segment, then
# concatenates. Idempotent-ish: re-run redownloads any short/missing part.
set -u
cd /data01/cris/projects/DAG/data/external/chembl || exit 1
URL="https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_37_sqlite.tar.gz"
TOTAL=5764252857
N=8
SEG=$(( (TOTAL + N - 1) / N ))

part_want() { local k=$1; local s=$((k*SEG)); local e=$((s+SEG-1)); [ $e -ge $TOTAL ] && e=$((TOTAL-1)); echo $((e-s+1)); }

dl_part() {
  local k=$1; local s=$((k*SEG)); local e=$((s+SEG-1)); [ $e -ge $TOTAL ] && e=$((TOTAL-1))
  local want=$((e-s+1)) got
  for try in 1 2 3 4 5 6 7 8; do
    got=$(stat -c %s "part_$k" 2>/dev/null || echo 0)
    [ "$got" = "$want" ] && return 0
    curl -s --retry 8 --retry-delay 5 -r "${s}-${e}" "$URL" -o "part_$k"
    got=$(stat -c %s "part_$k" 2>/dev/null || echo 0)
    [ "$got" = "$want" ] && return 0
    sleep 6
  done
  return 1
}

echo "start $(date '+%F %T') N=$N SEG=$SEG"
for k in $(seq 0 $((N-1))); do dl_part "$k" & done
wait

ok=1
for k in $(seq 0 $((N-1))); do
  want=$(part_want "$k"); got=$(stat -c %s "part_$k" 2>/dev/null || echo 0)
  echo "part_$k: $got / $want"
  [ "$got" = "$want" ] || ok=0
done

if [ "$ok" = 1 ]; then
  cat $(for k in $(seq 0 $((N-1))); do echo "part_$k"; done) > chembl_37_sqlite.tar.gz
  fs=$(stat -c %s chembl_37_sqlite.tar.gz)
  if [ "$fs" = "$TOTAL" ]; then
    rm -f part_*
    echo "DOWNLOAD_DONE size=$fs" > chembl_dl.status
  else
    echo "ASSEMBLE_FAIL size=$fs/$TOTAL" > chembl_dl.status
  fi
else
  echo "PARTS_FAIL" > chembl_dl.status
fi
echo "end $(date '+%F %T') status=$(cat chembl_dl.status)"
