#!/bin/bash
tempfile=$(mktemp)
cat - > "$tempfile"
lp -d PDF -U pi  "$tempfile"
rm "$tempfile"
