#include <application_and_shared-lib_export.h>

    APPLICATION_AND_SHARED_LIB_EXPORT
double colliding_variable = 11.11;

    APPLICATION_AND_SHARED_LIB_EXPORT
extern const double colliding_const = 12.12;

double colliding_func(double d) { return d + colliding_variable + colliding_const; }

    APPLICATION_AND_SHARED_LIB_EXPORT
double uses_colliding_in_library(double d) { return colliding_func(d); }

inline double colliding_inline(double d) { return 2.0 + d + colliding_variable + colliding_const; }

    APPLICATION_AND_SHARED_LIB_EXPORT
double uses_colliding_inline_in_library(double d) { return colliding_inline(d); }

static double local_variable_1 = 13.13;
static const double local_const_1 = 14.14;
static int local_function_1(int x) {
    return x*int(local_variable_1) + local_const_1;
}

namespace {
    double local_variable_2 = 15.15;
    const double local_const_2 = 16.16;
    int local_function_2(int x) {
        return x*int(local_variable_2) + local_const_2;
    }
}

    APPLICATION_AND_SHARED_LIB_EXPORT
int function_in_lib(int x) {
    return local_function_1(x) + local_function_2(x);
}
