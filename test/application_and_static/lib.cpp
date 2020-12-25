#ifndef _WIN32
static
#endif
double colliding_variable = 11.11;

#ifndef _WIN32
static
#else
extern
#endif
const double colliding_const = 12.12;

inline double colliding_inline(double d) { return 2.0 + d + colliding_variable + colliding_const; }
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

int function_in_lib(int x) {
    return local_function_1(x) + local_function_2(x);
}
