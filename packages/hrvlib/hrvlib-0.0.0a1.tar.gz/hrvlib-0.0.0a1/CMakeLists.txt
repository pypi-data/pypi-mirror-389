cmake_minimum_required(VERSION 3.15)
project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 CONFIG REQUIRED)
find_package(Eigen3 3.0 REQUIRED NO_MODULE)

pybind11_add_module(_core MODULE src/main.cpp)
target_link_libraries(_core PRIVATE Eigen3::Eigen)
install(TARGETS _core DESTINATION ${SKBUILD_PROJECT_NAME})
