#include <math/linalg/linalg_bindings.h>
#include <math/math_bindings.h>
#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace math {
void init_math(py::module_ &m) { math::linalg::init_linalg(m); }
}  // namespace math
