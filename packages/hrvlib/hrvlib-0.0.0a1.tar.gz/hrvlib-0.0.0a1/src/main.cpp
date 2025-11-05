#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include <Eigen/Dense>
#include <Eigen/Sparse>
#include <vector>

std::string hello_from_bin() { return "Hello from hrvlib!"; }

// Example function using Eigen for matrix operations
Eigen::VectorXd compute_mean_centered(const Eigen::VectorXd& vec) {
    double mean = vec.mean();
    return vec.array() - mean;
}

Eigen::VectorXd detrend(const Eigen::VectorXd& rr, double lambda_val = 10.0) {
    using T = double;
    using SpMat = Eigen::SparseMatrix<T>;
    using Triplet = Eigen::Triplet<T>;

    const Eigen::Index Tn = rr.size();
    if (Tn < 3) {
        // Nothing to detrend; mirror Python behavior gracefully.
        return Eigen::VectorXd::Zero(Tn);
    }

    // Build D2 ( (T-2) x T ) with diagonals [ +0:1, +1:-2, +2:1 ]
    SpMat D2(Tn - 2, Tn);
    {
        std::vector<Triplet> triplets;
        triplets.reserve(3 * static_cast<size_t>(Tn - 2));
        for (Eigen::Index i = 0; i < Tn - 2; ++i) {
            triplets.emplace_back(i, i,     T(1));   // diag offset +0
            triplets.emplace_back(i, i + 1, T(-2));  // diag offset +1
            triplets.emplace_back(i, i + 2, T(1));   // diag offset +2
        }
        D2.setFromTriplets(triplets.begin(), triplets.end());
        D2.makeCompressed();
    }

    // Compute D2^T * D2  (T x T), still sparse
    SpMat D2TD2 = SpMat(D2.transpose()) * D2;

    // Sparse identity I (T x T)
    SpMat I(Tn, Tn);
    I.setIdentity();

    // A = I + lambda^2 * (D2^T D2)
    const T lam2 = static_cast<T>(lambda_val * lambda_val);
    SpMat A = I + lam2 * D2TD2;

    // Solve A * z = rr  (symmetric positive definite)
    Eigen::SimplicialLDLT<SpMat> solver;
    solver.compute(A);
    if (solver.info() != Eigen::Success) {
        throw std::runtime_error("Failed to factorize system matrix.");
    }

    Eigen::VectorXd z = solver.solve(rr);
    if (solver.info() != Eigen::Success) {
        throw std::runtime_error("Failed to solve linear system.");
    }

    // Return rr - z (detrended signal)
    return rr - z;
}

// Example function for matrix multiplication
Eigen::MatrixXd matrix_multiply(const Eigen::MatrixXd& A, const Eigen::MatrixXd& B) {
    return A * B;
}

// Example function computing dot product
double vector_dot(const Eigen::VectorXd& a, const Eigen::VectorXd& b) {
    return a.dot(b);
}

namespace py = pybind11;

PYBIND11_MODULE(_core, m) {
  m.doc() = "pybind11 module with Eigen support for hrvlib";

  m.def("hello_from_bin", &hello_from_bin, R"pbdoc(
      A function that returns a Hello string.
  )pbdoc");

  m.def("compute_mean_centered", &compute_mean_centered,
      py::arg("vec"),
      R"pbdoc(
      Center a vector by subtracting its mean.

      Parameters
      ----------
      vec : numpy.ndarray
          Input vector

      Returns
      -------
      numpy.ndarray
          Mean-centered vector
  )pbdoc");

  m.def("detrend", &detrend,
      py::arg("vec"), py::arg("lambda_val") = 10.0,
      R"pbdoc(
      Center a vector by subtracting its mean.

      Parameters
      ----------
      vec : numpy.ndarray
          Input vector
      lambda_val : float, optional
      Returns
      -------
      numpy.ndarray
          Mean-centered vector
  )pbdoc");

  m.def("matrix_multiply", &matrix_multiply,
      py::arg("A"), py::arg("B"),
      R"pbdoc(
      Multiply two matrices using Eigen.

      Parameters
      ----------
      A : numpy.ndarray
          First matrix
      B : numpy.ndarray
          Second matrix

      Returns
      -------
      numpy.ndarray
          Product matrix A * B
  )pbdoc");

  m.def("vector_dot", &vector_dot,
      py::arg("a"), py::arg("b"),
      R"pbdoc(
      Compute dot product of two vectors.

      Parameters
      ----------
      a : numpy.ndarray
          First vector
      b : numpy.ndarray
          Second vector

      Returns
      -------
      float
          Dot product
  )pbdoc");
}
