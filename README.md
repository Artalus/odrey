# Odrey
![GHA check](https://github.com/Artalus/odrey/workflows/Test%20ODR/badge.svg)
===

## - What?
A Python script to check your C++ compiled stuff for [One Definition Rule](https://en.cppreference.com/w/cpp/language/definition) violations.

## - Why?
Because debugging ODRV is cumbersome and it's better to catch it at build-time rather than at run-time with [sanitizers](https://github.com/google/sanitizers/wiki/AddressSanitizerOneDefinitionRuleViolation).
<br>Sanitizers are awesome, though. Use sanitizers.
<br><sub><sup>at least hand sanitizers</sup></sub>

## - How?
By dumping symbols from compiled `.o`s, archived `.a`s and linked `.so` and ensuring that if they are called the same - they look the same.

## - What's the catch?
- proof of concept
- doesn't catch (kek) everything, is expected to catch more than needed
- potentially slow on large binaries
- works only on Linux (for the time being)

## - Whatever! I am convinced! Lets get started!
1. `pacman`, `yum`, `apt` or even `make` install yourself Python 3.6+ and `readelf` (usually in `binutils` package)
1. get `odr.py` somewhere you can execute it
1. run `odr.py object.o more/object.o and/libstatic.a and/even/libdynamic.so`
1. meditate on the output and see if it uncovers something nasty

### - Manually? Boring!
Best served hot and integrated with build system of your choice!

See `odr.cmake` for an example of integration with CMake.
