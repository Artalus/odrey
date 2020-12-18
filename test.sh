#!/bin/bash
cmake -S test -B build -GNinja
cmake --build build
