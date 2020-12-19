add_library(simple-inline-odr STATIC
foo.cpp
bar.cpp
)
add_executable(simple-inline-main main.cpp)
target_link_libraries(simple-inline-main simple-inline-odr)
