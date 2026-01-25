#!/usr/bin/env bash

for design in ./benchmarks/epfl/arithmetic/*.blif; do
  yosys-abc -c "
    read $design;
    strash;
    balance;
    if -K 6;
    print_stats;
  "
done

