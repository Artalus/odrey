set(_tool "\"${CMAKE_SOURCE_DIR}/../odr.py\" -Werror --")
foreach(lang C CXX)
   foreach(rule LINK_EXECUTABLE CREATE_SHARED_LIBRARY CREATE_SHARED_MODULE)
       set(CMAKE_${lang}_${rule}
           "${_tool} <OBJECTS> <LINK_LIBRARIES>"
           "${CMAKE_${lang}_${rule}}"
       )
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
endforeach()
