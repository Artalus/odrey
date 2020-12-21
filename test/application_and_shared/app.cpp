short colliding_variable = 21;
extern const short colliding_const = 22;
double colliding_func(double d) { return d + colliding_variable + colliding_const; }
double uses_colliding_in_app(double d) { return colliding_func(d); }
inline double colliding_inline(double d) { return 1.0 + d + colliding_variable + colliding_const; }
double uses_colliding_inline_in_app(double d) { return colliding_inline(d); }

static short local_variable_1 = 23;
static const short local_const_1 = 24;
static int local_function_1(int x) {
    return x*int(local_variable_1) + local_const_1;
}

namespace {
    short local_variable_2 = 25;
    const short local_const_2 = 26;
    int local_function_2(int x) {
        return x*int(local_variable_2) + local_const_2;
    }
}

int function_in_app(int x) {
    return local_function_1(x) + local_function_2(x);
}
