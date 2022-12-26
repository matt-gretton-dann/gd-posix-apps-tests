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
  echo "Usage: $0 awk_under_tests tests..." >& 2
  exit 2
fi
awk="$1"
shift

exit_code=0
while [ $# -ge 1 ];
do
  i="$1"
  shift
  $awk -f "$i" "test.countries" "test.countries" >"$run_dir/$i.output"
  if cmp -s "$i.expected" "$run_dir/$i.output"; then
    rm "$run_dir/$i.output"
  else
    echo "$i: FAIL"
    diff -b "$i.expected" "$run_dir/$i.output" | sed -e 's/^/	/' -e 10q
    exit_code=1
  fi
done

cd "$src_dir"
exit $exit_code
