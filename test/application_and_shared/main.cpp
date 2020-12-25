#include <iostream>
#include <application_and_shared-lib_export.h>

int function_in_app(int);
double uses_colliding_in_app(double);
double uses_colliding_inline_in_app(double);

    APPLICATION_AND_SHARED_LIB_EXPORT
int function_in_lib(int);
    APPLICATION_AND_SHARED_LIB_EXPORT
double uses_colliding_in_library(double);
    APPLICATION_AND_SHARED_LIB_EXPORT
double uses_colliding_inline_in_library(double);

    APPLICATION_AND_SHARED_LIB_EXPORT
extern short colliding_variable;
    APPLICATION_AND_SHARED_LIB_EXPORT
extern const short colliding_const;

int main() {
    std::cout << "colliding func in app: " << uses_colliding_in_app(0.0) << std::endl;
    std::cout << "colliding func in library: " << uses_colliding_in_library(0.0) << std::endl;
    std::cout << "colliding inline in app: " << uses_colliding_inline_in_app(0.0) << std::endl;
    std::cout << "colliding inline in library: " << uses_colliding_inline_in_library(0.0) << std::endl;
    std::cout << "colliding variable: " << colliding_variable << std::endl;
    std::cout << "colliding const: " << colliding_const << std::endl;
    std::cout << "function in lib: " << function_in_lib(10) << std::endl;
    std::cout << "function in app: " << function_in_app(10) << std::endl;
    return 0;
}
