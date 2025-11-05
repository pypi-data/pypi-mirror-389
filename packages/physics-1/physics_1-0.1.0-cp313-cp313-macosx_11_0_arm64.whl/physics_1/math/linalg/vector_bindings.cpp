#include <math/linalg/vector.h>
#include <math/linalg/vector_bindings.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

namespace math::linalg {
void init_vector2(py::module_ &m) {
  py::class_<Vector2>(m, "Vector2")
      .def(py::init<double, double>(), py::arg("x") = 0.0, py::arg("y") = 0.0)
      // members
      .def_property("x", py::overload_cast<>(&Vector2::x, py::const_),
                    py::overload_cast<const double &>(&Vector2::x))
      .def_property("y", py::overload_cast<>(&Vector2::y, py::const_),
                    py::overload_cast<const double &>(&Vector2::y))
      // overloads
      .def(py::self + py::self)
      .def(py::self += py::self)
      .def(py::self - py::self)
      .def(py::self -= py::self)
      .def(py::self * float())
      .def(py::self *= float())
      .def(float() * py::self)
      .def(py::self / float())
      .def(py::self /= float())
      .def(float() / py::self)
      .def(py::self == py::self)
      .def(py::self != py::self)
      .def(-py::self)
      // methods
      .def("mag", py::overload_cast<>(&Vector2::mag, py::const_))
      .def("unit", py::overload_cast<>(&Vector2::unit, py::const_))
      .def("angle", py::overload_cast<>(&Vector2::angle, py::const_))
      .def_static("from_mag_ang",
                  py::overload_cast<double, double>(&Vector2::from_mag_ang))
      .def("__repr__", &Vector2::to_string);
}
}  // namespace math::linalg
