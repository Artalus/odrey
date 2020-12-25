add_library(application_and_static-lib STATIC
lib.cpp
)
target_compile_definitions(application_and_static-lib PRIVATE application_and_static_lib_EXPORTS)
target_include_directories(application_and_static-lib PUBLIC ${CMAKE_CURRENT_BINARY_DIR})

add_executable(application_and_static
app.cpp
main.cpp
)
target_link_libraries(application_and_static PRIVATE
application_and_static-lib
)
