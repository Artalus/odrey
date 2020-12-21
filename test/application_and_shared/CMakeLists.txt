add_library(application_and_shared-lib SHARED
lib.cpp
)
add_executable(application_and_shared
app.cpp
main.cpp
)
target_link_libraries(application_and_shared PRIVATE
application_and_shared-lib
)
