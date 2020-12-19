cmake_minimum_required(VERSION 3.10)
project(odr)

include(../odr.cmake)

add_subdirectory(simple)
add_subdirectory(simple-inline)

add_custom_target(rebuild
    COMMAND "${CMAKE_COMMAND}" --build "${CMAKE_BINARY_DIR}" --target clean
    COMMAND "${CMAKE_COMMAND}" --build "${CMAKE_BINARY_DIR}"
    )
