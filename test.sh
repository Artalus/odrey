#!/bin/bash
cmake -S test -B build -GNinja
set -o pipefail
cmake --build build | tee output.txt
grep -Pz 'multiple definitions of func.*\n\s+in file .*foo.cpp.*\n\s+in file .*bar.cpp' output.txt
