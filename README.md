# Odrey
![GHA check](https://github.com/Artalus/odrey/workflows/Test%20ODR/badge.svg)
===

## - What?
A Python script to check your C++ compiled stuff for [One Definition Rule](https://en.cppreference.com/w/cpp/language/definition) violations.

## - Why?
Because debugging ODRV is cumbersome, not always trivial and it's better to catch it at build-time rather than at run-time with [sanitizers](https://github.com/google/sanitizers/wiki/AddressSanitizerOneDefinitionRuleViolation).
<br>Sanitizers are awesome, though. Use sanitizers.
<br><sub><sup>at least hand sanitizers</sup></sub>

It should be noted, that this task could be better done within compiler or linker themselves, where code model is available for more scrutinized analysis.
Ideally, we would like to have a compiler option, something like `-Wodr` and have violations reported before linking procedure. No known compiler does this.

## - How?
```c++
//foo.cpp
char func(char c) { return c; }
//bar.cpp
char func(char) { return 'b'; }
```
```cmake
add_library(foo STATIC foo.cpp)
add_library(bar STATIC bar.cpp)
target_link_libraries(app foo bar)
```
```
[6/6] Linking CXX executable app
multiple definitions of func(char):
  in file foo.cpp.o
  in file bar.cpp.o
```

## - But, technically how?
By dumping symbols from compiled `.o`s, archived `.a`s and linked `.so` and ensuring that there are no symbols having same signature and different implementation.

## - What's the catch?
- currently it is a proof of concept, not guaranteed to work for all cases
- doesn't catch everything, very likely to catch more than needed
- potentially slow on large binaries

## - Whatever! I am convinced! Lets get started!
1. - `if linux`: `pacman`, `yum`, `apt` or even `make` install yourself Python 3.6+, `readelf` and `c++filt` (usually in `binutils` package)
   - `if windows`: get `dumpbin.exe` from Visual Studio accessible in `PATH` envvar (e.g. via `vcvarsall.bat` or VS Command Prompt)
1. get `odr.py` someplace where you can execute it
1. run `odr.py object.o more/object.o and/libstatic.a and/even/libdynamic.so`
1. meditate on the output and see if it uncovers something nasty

### - Manually? Boring!
Best served hot and integrated with build system of your choice!

See `odr.cmake` for an example of integration with CMake.
