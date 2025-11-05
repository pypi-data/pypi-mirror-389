#include <example/functions_bindings.h>
#include <pybind11/pybind11.h>

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)

namespace py = pybind11;

PYBIND11_MODULE(_example, m, py::mod_gil_not_used(),
                py::multiple_interpreters::per_interpreter_gil()) {
  m.doc() = R"pbdoc(
        Physics 1 Example Module
        -----------------------

        .. currentmodule:: physics_1

        .. autosummary::
           :toctree: _generate
    )pbdoc";

  example::functions::init_functions(m);

#ifdef VERSION_INFO
  m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
  m.attr("__version__") = "dev";
#endif
}
