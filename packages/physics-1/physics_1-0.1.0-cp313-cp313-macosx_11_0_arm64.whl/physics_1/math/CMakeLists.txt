python_add_library(
  _math
  MODULE
  main.cpp
  math_bindings.cpp
  linalg/linalg_bindings.cpp
  linalg/vector_bindings.cpp
  WITH_SOABI)

# This is passing in the version as a define just as an example
target_compile_definitions(_math PRIVATE VERSION_INFO=${PROJECT_VERSION})
target_link_libraries(_math PRIVATE pybind11::headers linalg)

# The install directory is the output (wheel) directory
install(TARGETS _math DESTINATION physics_1/math)
