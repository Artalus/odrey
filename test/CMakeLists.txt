cmake_minimum_required(VERSION 3.10)
project(odr)
include(GenerateExportHeader)

include(../odr.cmake)

add_subdirectory(simple)
add_subdirectory(application_and_shared)
