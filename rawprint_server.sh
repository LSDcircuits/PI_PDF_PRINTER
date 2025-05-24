#!/bin/bash

while true; do
  nc -l -p 9100 | /usr/local/bin/rawprint.sh
done
