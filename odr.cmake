# TODO: provide way to setup flags
set(_tool "\"${CMAKE_SOURCE_DIR}/../odr.py\" --")
if(MSVC)
    # TODO: provide way to setup path to python
    # without explicitly specifying python, windows can turn it into noop
    set(_tool "python ${_tool}")
endif()

set(_rules LINK_EXECUTABLE CREATE_SHARED_LIBRARY CREATE_SHARED_MODULE)
if(MSVC)
    list(APPEND _rules CREATE_STATIC_LIBRARY)
endif()

foreach(lang C CXX)
    foreach(rule IN LISTS _rules)
        set(CMAKE_${lang}_${rule}
            "${_tool} <OBJECTS> <LINK_LIBRARIES>"
            "${CMAKE_${lang}_${rule}}"
        )
        message("CMAKE_${lang}_${rule}:: ${CMAKE_${lang}_${rule}}")
    endforeach()
    # using ARCHIVE_x instead of CREATE_STATIC_LIBRARY - when latter is not empty, it completely overrides first
    # see <cmake>/Modules/CMakeCXXInformation.cmake for details
    set(CMAKE_${lang}_ARCHIVE_CREATE
        "${_tool} <OBJECTS>"
        "${CMAKE_${lang}_ARCHIVE_CREATE}"
    )
    set(CMAKE_${lang}_ARCHIVE_APPEND
        "${_tool} <OBJECTS> <TARGET>"
        "${CMAKE_${lang}_ARCHIVE_APPEND}"
    )
    foreach(rule ARCHIVE_CREATE ARCHIVE_APPEND)
        message("CMAKE_${lang}_${rule}:: ${CMAKE_${lang}_${rule}}")
    endforeach()
endforeach()
