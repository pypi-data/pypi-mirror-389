python_add_library(_example MODULE main.cpp example_bindings.cpp WITH_SOABI)

# This is passing in the version as a define just as an example
target_compile_definitions(_example PRIVATE VERSION_INFO=${PROJECT_VERSION})
target_link_libraries(_example PRIVATE pybind11::headers example)

# The install directory is the output (wheel) directory
install(TARGETS _example DESTINATION physics_1/example)
