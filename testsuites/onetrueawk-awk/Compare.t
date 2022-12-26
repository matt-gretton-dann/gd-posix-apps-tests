#!/bin/sh
# Original script:
# Copyright 1997 Lucent Technologies.  See LICENCE for licensing information.
#
# Modifications:
# Copyright 2022 Matthew Gretton-Dann
# Licence: SPDX Identifier: Apache-2.0

set -eu

run_dir="$(pwd)"
cd "$(dirname "$0")"
src_dir="$(pwd)"

if [ $# -lt 2 ]; then
  echo "Usage: $0 awk_under_test tests..." >& 2
  exit 2
fi
awk="$1"
shift

exit_code=0
while [ $# -ge 1 ];
do
  i="$1"
  shift
  ec=0
  $awk -f "$i" "test.data" >"$run_dir/$i.output" || ec=$?
  if [ "$i" = "T.exit" ]; then
    expected_ec=1
  elif [ "$i" = "T.exit1" ]; then
    expected_ec=2
  else
    expected_ec=0
  fi
  if [ "$expected_ec" -ne "$ec" ]; then
    echo "$i: FAIL - exit code"
  fi
  if cmp -s "$i.expected" "$run_dir/$i.output"; then
    rm "$run_dir/$i.output"
  else
    echo "$i: FAIL - expected output"
    diff -b "$i.expected" "$run_dir/$i.output" | sed -e 's/^/	/' -e 10q
    exit_code=1
  fi
done

cd "$src_dir"
exit $exit_code
