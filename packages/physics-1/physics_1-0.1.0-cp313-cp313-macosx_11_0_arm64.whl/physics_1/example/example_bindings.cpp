#include <example/functions.h>
#include <example/functions_bindings.h>

namespace example::functions {
void init_functions(py::module_ &m) {
  m.def_submodule("functions", "Some example functions demoing pybind11")
      .def("add", &example::functions::add, py::arg("i"), py::arg("j"), R"pbdoc(
        Add two numbers
      )pbdoc")
      .def("sub", &example::functions::sub, py::arg("i"), py::arg("j"), R"pbdoc(
        Subtract two numbers
      )pbdoc")
      .def("mul", &example::functions::mul, py::arg("i"), py::arg("j"), R"pbdoc(
        Multiply two numbers
      )pbdoc")
      .def("div", &example::functions::div, py::arg("i"), py::arg("j"), R"pbdoc(
        Divide two numbers
      )pbdoc");
}
}  // namespace example::functions
