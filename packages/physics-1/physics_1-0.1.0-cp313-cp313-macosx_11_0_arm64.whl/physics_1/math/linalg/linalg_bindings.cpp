#include <math/linalg/linalg_bindings.h>
#include <math/linalg/vector_bindings.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace math::linalg {
void init_linalg(py::module_ &m) {
  auto linalg = m.def_submodule("linalg", "A general linear algebra library");

  math::linalg::init_vector2(linalg);
}
}  // namespace math::linalg
