// src/repsim_bindings.cpp
#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <stdexcept>
#include "repsim_core.hpp"

namespace py = pybind11;
using repsim::Index;
using repsim::Mat;

// convert python sequence of arrays -> std::vector<repsim::Mat> row-major copy
static std::vector<Mat> list_to_eigen(const py::sequence &mats)
{
    std::vector<Mat> Xs;
    Xs.reserve(py::len(mats));
    for (auto obj : mats)
    {
        // pybind11 automatically casts NumPy arrays to Eigen::MatrixXd
        Eigen::MatrixXd X = py::cast<Eigen::MatrixXd>(obj);
        Xs.emplace_back(X); // copy into row-major Mat
    }
    return Xs;
}

// major interface
PYBIND11_MODULE(_repsim, m)
{
    // 1. linear regression
    m.def("cpp_linreg", [](const py::sequence &mats)
          { return repsim::core_LinReg(list_to_eigen(mats)); });

    // 2. dot product
    m.def("cpp_dot_product", [](const py::sequence &mats)
          { return repsim::core_DotProduct(list_to_eigen(mats)); });

    // 3. HSIC
    m.def("cpp_hsic", [](const py::sequence &mats, const std::string &kernel, const std::string &estimator)
          { return repsim::core_HSIC(list_to_eigen(mats), kernel, estimator); });

    // 4. CKA
    m.def("cpp_cka", [](const py::sequence &mats, const std::string &kernel, const std::string &estimator)
          { return repsim::core_CKA(list_to_eigen(mats), kernel, estimator); });

    // 5. CCA
    m.def("cpp_cca", [](const py::sequence &mats, const std::string &type)
          { return repsim::core_CCA(list_to_eigen(mats), type); });

    // 6. SVCCA
    m.def("cpp_svcca", [](const py::sequence &mats, const std::string &type)
          { return repsim::core_SVCCA(list_to_eigen(mats), type); });

    // 7. PWCCA
    m.def("cpp_pwcca", [](const py::sequence &mats)
          { return repsim::core_PWCCA(list_to_eigen(mats)); });
}