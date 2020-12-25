if(NOT ODREY_SCRIPT_PATH)
    set(ODREY_SCRIPT_PATH "${CMAKE_BINARY_DIR}/odr.py")
endif()
if (NOT EXISTS ${ODREY_SCRIPT_PATH})
    message(FATAL_ERROR "Could not found ${ODREY_SCRIPT_PATH}"
    "To use odr.cmake module, put `odr.py` script to binary dir, "
    "or specify its path via ODREY_SCRIPT_PATH cmake variable")
endif()



set(_tool "\"${ODREY_SCRIPT_PATH}\"")
if(NOT ODREY_PYTHON_EXE AND WIN32)
    # without explicitly specifying python, windows can turn the call into noop
    set(ODREY_PYTHON_EXE "python")
endif()
if (ODREY_PYTHON_EXE)
    string(PREPEND _tool "${ODREY_PYTHON_EXE} ")
endif()
if (ODREY_WRITE_JSON)
    string(APPEND _tool " --output-json <TARGET>.json --target <TARGET>")
endif()
string(APPEND _tool " --")



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
