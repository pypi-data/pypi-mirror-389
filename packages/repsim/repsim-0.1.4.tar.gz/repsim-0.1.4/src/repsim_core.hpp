// MAIN HEADER
//  Basic Typedefs
//  Utilities
//    util_median --------- compute the median of a vector
//    util_ONB ------------ polar decomposition to get orthonormal basis
//    util_distmat -------- compute pairwise distance matrix
//    util_upper_median --- given D, compute median of all entries in the upper triangle
//    util_upper_mean ----- given D, compute mean of all entries in the upper triangle
//    util_nuclear_norm --- compute nuclear norm of a matrix
//    util_centering ------ return a mean centered version of input matrix
//    util_SVD_denoise ---- denoise by explained variance (centered input case)
//    util_HSIC_estimator - different types of estimators for HSIC
//  Kernel
//    kernel_linear ------ linear kernel
//    kernel_rbf --------- median heuristic for RBF kernel
//    kernel_rbf_mean ---- mean heuristic for RBF kernel
//    kernel_rbf_dual ---- dual median form RBF kernel
//    kernel_select ------ select kernel by string ========== update iteratively
//  Core Computation with multiple inputs
//    core_DotProduct ---- squared dot product between inputs
//    core_LinReg -------- R^2
//    core_HSIC ---------- HSIC
//    core_CKA ----------- CKA
//    core_CCA ----------- CCA
//    core_SVCCA --------- singular vector CCA
//    core_PWCCA --------- projection weighted CCA

#pragma once
#include <Eigen/Core>
#include <Eigen/SVD>
#include <algorithm>
#include <stdexcept>
#include <limits>
#include <string>
#include <cmath>
#include <vector>

namespace repsim
{
  // --------------------------------
  // [1] Basic Typedefs
  // --------------------------------
  using Index = Eigen::Index;
  using Mat = Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>;
  using Vec = Eigen::VectorXd;

  // --------------------------------
  // [2] Utilities
  // --------------------------------
  inline double util_median(std::vector<double> vals)
  {
    const size_t n = vals.size();
    if (n == 0)
      return std::numeric_limits<double>::quiet_NaN();

    auto mid = vals.begin() + n / 2;
    std::nth_element(vals.begin(), mid, vals.end());
    const double upper_mid = *mid;

    if (n % 2 == 1)
    {
      // Odd number of elements → middle element
      return upper_mid;
    }
    else
    {
      // Even number of elements → need lower middle too
      const auto lower_mid_it = std::max_element(vals.begin(), mid);
      const double lower_mid = *lower_mid_it;
      return 0.5 * (lower_mid + upper_mid);
    }
  }

  inline Mat util_ONB(const Mat &X)
  {
    // threshold
    double rel_tol = 1e-12;

    // Thin SVD: X = U Σ Vᵀ
    Eigen::JacobiSVD<Mat> svd(X, Eigen::ComputeThinU | Eigen::ComputeThinV);
    const Eigen::VectorXd s = svd.singularValues();
    const double smax = (s.size() > 0) ? s.maxCoeff() : 0.0;

    // Rank estimation
    const double thresh = rel_tol * smax;
    Eigen::Index r = 0;
    for (Eigen::Index k = 0; k < s.size(); ++k)
    {
      if (s[k] > thresh)
        ++r;
    }

    // Empty case: all singular values below threshold
    if (r == 0)
      return Mat::Zero(X.rows(), 0);

    // Return orthonormal basis for Col(X)
    return svd.matrixU().leftCols(r);
  }

  inline Mat util_distmat(const Mat &X)
  {
    // X: n × p (rows are samples)
    Mat G = X * X.transpose(); // Gram
    Vec d = G.diagonal();      // row-wise squared norms
    Mat D = (-2.0 * G);
    D.colwise() += d;             // add ||x_j||^2 to each column
    D.rowwise() += d.transpose(); // add ||x_i||^2 to each row
    // numerical guard
    D = D.cwiseMax(0.0);
    D = D.array().sqrt().matrix(); // pairwise distances
    return D;
  }

  inline double util_upper_median(const Mat &D)
  {
    const Index n = D.rows();

    std::vector<double> vals; // vector of upper triangles
    vals.reserve(static_cast<size_t>(n) * (n - 1) / 2);
    for (Index i = 0; i < (n - 1); i++)
    { // assign process
      for (Index j = (i + 1); j < n; j++)
      {
        vals.emplace_back(D(i, j));
      }
    }

    if (vals.empty())
    {
      return (0.0);
    }

    return (util_median(vals));
  }

  inline double util_upper_mean(const Mat &D)
  {
    const Index n = D.rows();
    if (n < 2)
      return 0.0;

    double sum = 0.0;
    size_t count = 0;

    for (Index i = 0; i < n - 1; ++i)
    {
      for (Index j = i + 1; j < n; ++j)
      {
        sum += D(i, j);
        ++count;
      }
    }

    return (count > 0) ? (sum / static_cast<double>(count)) : 0.0;
  }
  inline double util_nuclear_norm(const Mat &X)
  {
    Eigen::JacobiSVD<Mat> svd(X); // simply, singular values only
    // Eigen::JacobiSVD<Mat> svd(X, Eigen::ComputeThinU | Eigen::ComputeThinV); // full svd
    return (svd.singularValues().sum());
  }
  inline Mat util_centering(const Mat &X)
  {
    // const Index n = X.rows();
    // const Index p = X.cols();
    // Mat X_centered = X;
    // Vec col_means = X.colwise().mean();
    // for (Index j=0; j<p; j++){
    //   X_centered.col(j).array() -= col_means(j);
    // }
    // return(X_centered);
    // Center columns (subtract column means)
    return X.rowwise() - X.colwise().mean();
  }
  inline Mat util_SVD_denoise(const Mat &X, double var_thresh = 0.99)
  {
    // guard and clamp threshold
    if (var_thresh < 0.0)
    {
      var_thresh = 0.000000001;
    }
    if (var_thresh > 1.0)
    {
      var_thresh = 0.999999999;
    }

    const Index n = X.rows(), p = X.cols();
    if (n == 0 || p == 0)
      return Mat::Zero(n, p);

    // Thin SVD: X = U Σ V^T
    Eigen::JacobiSVD<Mat> svd(X, Eigen::ComputeThinU | Eigen::ComputeThinV);
    const Vec s = svd.singularValues(); // length = k = min(n, p)
    if (s.size() == 0)
      return Mat::Zero(n, p);

    // Choose minimal r with cumulative variance >= var_thresh
    // variance ~ s_i^2
    const Vec s2 = s.array().square().matrix();
    const double total = s2.sum();
    if (total <= 0.0)
      return Mat::Zero(n, p);

    Index r = 1;
    double cum = s2[0];
    while (r < s2.size() && (cum / total) < var_thresh)
    {
      cum += s2[r];
      ++r;
    }

    // Truncated factors
    const Mat U_r = svd.matrixU().leftCols(r); // n x r
    const Mat V_r = svd.matrixV().leftCols(r); // p x r
    const Mat Sr = s.head(r).asDiagonal();     // r x r

    // Low-rank reconstruction: X_r = U_r Σ_r V_r^T  (same shape as X)
    return U_r * Sr * V_r.transpose();
  }

  // https://openreview.net/pdf?id=vyRAYoxUuA
  inline double util_HSIC_gretton(const Mat &Kx, const Mat &Ky)
  {
    const Index N = Kx.rows();
    const Mat H = Mat::Identity(N, N) - (Mat::Ones(N, N) / static_cast<double>(N));

    double NN = static_cast<double>(N);
    double denom = (NN - 1.0) * (NN - 1.0);
    double hsic = (Kx * H * Ky * H).trace() / denom;
    return (hsic);
  }
  inline double util_HSIC_song(const Mat &Kx_, const Mat &Ky_)
  {
    const Index n = Kx_.rows();
    if (n < 4)
    {
      // Unbiased estimator needs n >= 4. Choose a biased version
      return (util_HSIC_gretton(Kx_, Ky_));
    }

    // assign for inplace zeroing out
    Mat Kx = Kx_;
    Mat Ky = Ky_;

    // Ensure diagonals are zero (required by the unbiased formula).
    Kx.diagonal().setZero();
    Ky.diagonal().setZero();

    // Convenience constants
    const double nd = static_cast<double>(n);
    const double denom_main = nd * (nd - 3.0);
    const double inv_nm1_nm2 = 1.0 / ((nd - 1.0) * (nd - 2.0));
    const double coef_cross = 2.0 / (nd - 2.0);

    // term1: tr(K L) == sum_ij K_ij * L_ij (for symmetric K,L)
    const double term1 = (Kx.cwiseProduct(Ky)).sum();

    // Ones vector
    Vec ones = Vec::Ones(n);

    // sK = K * 1, sL = L * 1
    const Vec sK = Kx * ones;
    const Vec sL = Ky * ones;

    // term2: [(1^T K 1)(1^T L 1)] / [(n-1)(n-2)]
    const double sumK = sK.sum();
    const double sumL = sL.sum();
    const double term2 = (sumK * sumL) * inv_nm1_nm2;

    // term3: [2/(n-2)] * (1^T K L 1) = [2/(n-2)] * (sK dot sL)
    const double term3 = coef_cross * sK.dot(sL);

    // Combine
    const double hsic_u = (term1 + term2 - term3) / denom_main;

    return hsic_u;
  }
  // HSIC estimator of Lange et al. (2023).
  // Inputs: symmetric Gram matrices Kx, Ky (n x n), any diagonals acceptable.
  // Returns: scalar HSIC_Lange. Requires n >= 4.
  inline double util_HSIC_lange(const Mat &Kx, const Mat &Ky)
  {
    const Index n = Kx.rows();
    if (n < 4)
    {
      return (util_HSIC_gretton(Kx, Ky));
    }

    // Center: Kc = H Kx H, Lc = H Ky H, with H = I - 11^T/n
    const double nd = static_cast<double>(n);
    Mat H = Mat::Identity(n, n) - Mat::Ones(n, n) / nd;
    Mat Kc = H * Kx * H;
    Mat Lc = H * Ky * H;

    // Strict-lower-triangular Frobenius inner product: sum_{i>j} Kc_ij * Lc_ij
    double s = 0.0;
    for (Index i = 1; i < n; ++i)
    {
      // dot of row i lower part (0..i-1)
      s += Kc.row(i).head(i).dot(Lc.row(i).head(i));
    }

    // Scale
    return (2.0 / (nd * (nd - 3.0))) * s;
  }

  inline double util_HSIC_estimator(const Mat &Kx, const Mat &Ky,
                                    const std::string &type = "gretton")
  {
    if (type == "gretton")
    {
      return (util_HSIC_gretton(Kx, Ky));
    }
    else if (type == "song")
    {
      return (util_HSIC_song(Kx, Ky));
    }
    else if (type == "lange")
    {
      return (util_HSIC_lange(Kx, Ky));
    }
    else
    {
      throw std::invalid_argument("util_HSIC_estimator: unknown HSIC estimator type '" + type + "'");
    }
  }

  // --------------------------------
  // [3] Kernel
  // --------------------------------
  inline Mat kernel_linear(const Mat &X)
  {
    Mat X_centered = util_centering(X);
    return (X_centered * X_centered.transpose());
  }
  inline Mat kernel_rbf(const Mat &X)
  {
    // compute the distance matrix
    const Mat D = util_distmat(X);

    // get the bandwidth
    double sigma = util_upper_median(D);
    double sig2 = std::max(sigma * sigma, 1e-12);

    // compute the kernel matrix
    const Mat D2 = D.array().square().matrix();
    Mat K = (-D2.array() / (2.0 * sig2)).exp().matrix();
    K.diagonal().setOnes();
    return (K);
  }
  inline Mat kernel_rbf_mean(const Mat &X)
  {
    // distance matrix and bandwidth
    const Mat D2 = util_distmat(X).array().square().matrix();
    const double mean_sq = util_upper_mean(D2);
    const double denom = std::max(mean_sq, 1e-12);

    Mat K = (-D2.array() / denom).exp().matrix();
    K.diagonal().setOnes();
    return (K);
  }
  inline Mat kernel_rbf_dualmed(const Mat &X)
  {
    const Index N = X.rows();
    const Mat D = util_distmat(X);

    // find median of each row
    std::vector<double> row_medians;
    row_medians.reserve(N);
    for (Index i = 0; i < N; i++)
    {
      std::vector<double> row_vals;
      row_vals.reserve(N - 1);
      for (Index j = 0; j < N; j++)
      {
        if (i != j)
        {
          row_vals.emplace_back(D(i, j));
        }
      }
      row_medians.emplace_back(util_median(row_vals));
    }

    // compute the kernel
    Mat K = Mat::Zero(N, N);
    for (Index i = 0; i < (N - 1); i++)
    {
      for (Index j = (i + 1); j < N; j++)
      {
        double denom = 2.0 * row_medians[i] * row_medians[j];
        denom = std::max(denom, 1e-12);
        K(i, j) = std::exp(-(D(i, j) * D(i, j)) / denom);
        K(j, i) = K(i, j);
      }
    }
    K.diagonal().setOnes();
    return (K);
  }

  // --------------------------------
  // [4] Computation with multiple inputs
  // --------------------------------
  inline Mat core_LinReg(const std::vector<Mat> &Xs)
  {
    // prep
    const Index M = static_cast<Index>(Xs.size());
    Mat output = Mat::Ones(M, M);

    // batch compute
    std::vector<Mat> Qs;
    Qs.reserve(M);
    std::vector<double> X_sqnorms;
    X_sqnorms.reserve(M);
    for (Index i = 0; i < M; i++)
    {
      Qs.emplace_back(util_ONB(Xs[i]));
      X_sqnorms.emplace_back((Xs[i]).squaredNorm());
    }

    // compute off-diagonals
    for (Index i = 0; i < M; i++)
    {
      const Mat &now_Q = Qs[i];
      for (Index j = 0; j < M; j++)
      {
        const Mat &now_X = Xs[j];
        const double denom = X_sqnorms[j];
        if (denom > 0.0)
        {
          output(i, j) = (now_Q.transpose() * now_X).squaredNorm() / denom;
        }
        else
        {
          output(i, j) = 0.0;
        }
      }
    }

    // symmetrize
    for (Index i = 0; i < (M - 1); i++)
    {
      for (Index j = (i + 1); j < M; j++)
      {
        double val_ij = output(i, j);
        double val_ji = output(j, i);
        output(i, j) = (val_ij + val_ji) / 2.0;
        output(j, i) = output(i, j);
      }
    }

    // return the output
    return (output);
  }
  // kernel_select : iteratively modify
  //  in R, check "auxiliary/aux_list_kernels"
  inline Mat kernel_select(const Mat &X,
                           const std::string &type)
  {
    if (type == "linear")
    {
      return (kernel_linear(X));
    }
    else if (type == "rbf")
    {
      return (kernel_rbf(X));
    }
    else if (type == "rbf_mean")
    {
      return (kernel_rbf_mean(X));
    }
    else if (type == "rbf_dualmed")
    {
      return (kernel_rbf_dualmed(X));
    }
    else
    {
      throw std::invalid_argument("kernel_select: unknown kernel type '" + type + "'");
    }
  }

  inline Mat core_DotProduct(const std::vector<Mat> &Xs)
  {
    // prep
    const Index M = static_cast<Index>(Xs.size());
    Mat output = Mat::Zero(M, M);

    // compute diagonal
    double val = 0.0;
    for (Index i = 0; i < M; i++)
    {
      val = (Xs[i].transpose() * Xs[i]).squaredNorm();
      output(i, i) = val;
    }

    // compute off-diagonal
    for (Index i = 0; i < (M - 1); i++)
    {
      for (Index j = (i + 1); j < M; j++)
      {
        val = (Xs[j].transpose() * Xs[i]).squaredNorm();
        output(i, j) = val;
        output(j, i) = val;
      }
    }

    // return the output
    return (output);
  }

  inline Mat core_HSIC(const std::vector<Mat> &Xs,
                       const std::string &type,
                       const std::string &estimator)
  {
    // prep
    const Index M = static_cast<Index>(Xs.size());
    Mat output = Mat::Zero(M, M);

    // precompute - kernels at batch
    std::vector<Mat> batch_K;
    batch_K.reserve(M);
    for (Index i = 0; i < M; i++)
    {
      batch_K.emplace_back(kernel_select(Xs[i], type));
    }

    // compute - diagonal
    for (Index m = 0; m < M; m++)
    {
      output(m, m) = util_HSIC_estimator(batch_K[m], batch_K[m], estimator);
    }
    for (Index i = 0; i < (M - 1); i++)
    {
      for (Index j = (i + 1); j < M; j++)
      {
        double val = util_HSIC_estimator(batch_K[i], batch_K[j], estimator);
        output(i, j) = val;
        output(j, i) = val;
      }
    }

    // return
    return (output);
  }

  inline Mat core_CKA(const std::vector<Mat> &Xs,
                      const std::string &kernel_type,
                      const std::string &estimator)
  {

    const Index M = static_cast<Index>(Xs.size());

    // Precompute kernels
    std::vector<Mat> K;
    K.reserve(M);
    for (Index i = 0; i < M; ++i)
      K.emplace_back(kernel_select(Xs[i], kernel_type));

    // Compute HSIC matrix with requested estimator
    Mat HSIC_mat = Mat::Zero(M, M);
    for (Index i = 0; i < M; ++i)
    {
      for (Index j = i; j < M; ++j)
      {
        double v = util_HSIC_estimator(K[i], K[j], estimator);
        HSIC_mat(i, j) = v;
        HSIC_mat(j, i) = v;
      }
    }

    // For normalization, use stable diagonals (prefer Gretton)
    Vec diag = Vec::Zero(M);
    for (Index i = 0; i < M; ++i)
    {
      double d = util_HSIC_gretton(K[i], K[i]); // force Gretton here
      // guard against tiny/negative numerical values
      diag[i] = std::max(d, 1e-12);
    }

    // Build CKA
    Mat out = Mat::Zero(M, M);
    out.diagonal().setOnes();
    for (Index i = 0; i < M - 1; ++i)
    {
      for (Index j = i + 1; j < M; ++j)
      {
        double denom = std::sqrt(diag[i] * diag[j]);
        double val = (denom > 0.0) ? (HSIC_mat(i, j) / denom) : 0.0;
        out(i, j) = val;
        out(j, i) = val;
      }
    }
    return out;
  }

  inline Mat core_CCA(const std::vector<Mat> &Xs,
                      const std::string &type)
  {
    const Index M = static_cast<Index>(Xs.size()); // number of reps
    std::vector<Mat> vec_Q;
    vec_Q.reserve(M); // batch compute ONBs
    std::vector<double> vec_dims;
    vec_dims.reserve(M);
    for (Index m = 0; m < M; m++)
    {
      Mat now_X = util_ONB(Xs[m]);                              // get the current matrix
      vec_dims.emplace_back(static_cast<double>(now_X.cols())); // current dim

      Mat X_center = util_centering(now_X);   // mean center
      vec_Q.emplace_back(util_ONB(X_center)); // get the ONB of centered matrix
    }

    Mat output = Mat::Zero(M, M);
    // compute the diagonals
    for (Index m = 0; m < M; m++)
    {
      const Mat Qx = vec_Q[m];
      if (type == "yanai")
      {
        output(m, m) = (Qx.transpose() * Qx).squaredNorm() / vec_dims[m];
      }
      else if (type == "pillai")
      {
        output(m, m) = util_nuclear_norm(Qx.transpose() * Qx) / vec_dims[m];
      }
      else
      {
        throw std::invalid_argument("core_CCA: unknown CCA type '" + type + "'");
      }
    }

    // compute the off-diagonals
    for (Index i = 0; i < (M - 1); i++)
    {
      const Mat Qx = vec_Q[i];
      for (Index j = (i + 1); j < M; j++)
      {
        const Mat Qy = vec_Q[j];
        if (type == "yanai")
        { // yanai
          double denom = std::min(vec_dims[i], vec_dims[j]);
          double val = (Qx.transpose() * Qy).squaredNorm() / denom;
          output(i, j) = val;
          output(j, i) = val;
        }
        else
        { // just pillai
          double denom = std::min(vec_dims[i], vec_dims[j]);
          double val = util_nuclear_norm(Qx.transpose() * Qy) / denom;
          output(i, j) = val;
          output(j, i) = val;
        }
      }
    }
    return (output);
  }

  inline Mat core_SVCCA(const std::vector<Mat> &Xs,
                        const std::string &type)
  {
    const Index M = static_cast<Index>(Xs.size()); // number of reps
    std::vector<Mat> vec_Q;
    vec_Q.reserve(M); // batch compute ONBs
    std::vector<double> vec_dims;
    vec_dims.reserve(M);
    for (Index m = 0; m < M; m++)
    {
      Mat now_X = util_ONB(Xs[m]);                              // get the current matrix
      vec_dims.emplace_back(static_cast<double>(now_X.cols())); // current dim

      Mat X_center = util_centering(now_X);       // mean center
      Mat X_denoise = util_SVD_denoise(X_center); // svd denoise
      vec_Q.emplace_back(util_ONB(X_denoise));    // get the ONB of denoised matrix
    }

    Mat output = Mat::Zero(M, M);
    // compute the diagonals
    for (Index m = 0; m < M; m++)
    {
      const Mat Qx = vec_Q[m];
      if (type == "yanai")
      {
        output(m, m) = (Qx.transpose() * Qx).squaredNorm() / vec_dims[m];
      }
      else if (type == "pillai")
      {
        output(m, m) = util_nuclear_norm(Qx.transpose() * Qx) / vec_dims[m];
      }
      else
      {
        throw std::invalid_argument("core_CCA: unknown CCA type '" + type + "'");
      }
    }

    // compute the off-diagonals
    for (Index i = 0; i < (M - 1); i++)
    {
      const Mat Qx = vec_Q[i];
      for (Index j = (i + 1); j < M; j++)
      {
        const Mat Qy = vec_Q[j];
        if (type == "yanai")
        { // yanai
          double denom = std::min(vec_dims[i], vec_dims[j]);
          double val = (Qx.transpose() * Qy).squaredNorm() / denom;
          output(i, j) = val;
          output(j, i) = val;
        }
        else
        { // just pillai
          double denom = std::min(vec_dims[i], vec_dims[j]);
          double val = util_nuclear_norm(Qx.transpose() * Qy) / denom;
          output(i, j) = val;
          output(j, i) = val;
        }
      }
    }
    return (output);
  }

  // --------------------------------
  // [5] PWCCA (Projection-Weighted CCA)
  // --------------------------------
  //
  // References/recipe:
  // - Center columns of X,Y (n x p), (n x q)
  // - Thin SVDs: Xc = Ux Sx Vx^T,  Yc = Uy Sy Vy^T
  // - Compute M = Ux^T Uy; SVD: M = L Σ R^T
  // - Canonical correlations: diag(Σ) (length r)
  // - Canonical variates (sample-space): UxQx = Ux * L,  UyQy = Uy * R
  // - Projection weights for X-side:
  //     C = (UxQx)^T Xc   [shape: r x p]
  //     w_i = sum_j |C_{i,j}|,  then normalize so sum_i w_i = 1
  // - PWCCA(X,Y) = sum_i w_i * Σ_i
  //
  // Notes:
  // - r = min(rank(Xc), rank(Yc)). Rank is estimated with relative tol to largest singular value.
  // - If total weight is zero (degenerate), fall back to uniform weights over r.
  // - Returns similarity in [0,1]. A distance variant is (1 - PWCCA).

  inline double core_PWCCA_pair(const Mat &X, const Mat &Y)
  {
    // 0) parameter
    double rel_tol = 1e-12;

    // 1) Center columns
    const Mat Xc = util_centering(X);
    const Mat Yc = util_centering(Y);

    const Index n = Xc.rows();
    if (n == 0 || Xc.cols() == 0 || Yc.cols() == 0)
    {
      return 0.0;
    }

    // 2) Thin SVDs
    Eigen::JacobiSVD<Mat> svdX(Xc, Eigen::ComputeThinU | Eigen::ComputeThinV);
    Eigen::JacobiSVD<Mat> svdY(Yc, Eigen::ComputeThinU | Eigen::ComputeThinV);

    const Vec sX = svdX.singularValues();
    const Vec sY = svdY.singularValues();
    const double sXmax = (sX.size() > 0 ? sX.maxCoeff() : 0.0);
    const double sYmax = (sY.size() > 0 ? sY.maxCoeff() : 0.0);
    if (sXmax <= 0.0 || sYmax <= 0.0)
    {
      return 0.0;
    }

    // Rank thresholds
    const double tX = rel_tol * sXmax;
    const double tY = rel_tol * sYmax;

    Index rX = 0, rY = 0;
    for (Index i = 0; i < sX.size(); ++i)
      if (sX[i] > tX)
        ++rX;
    for (Index i = 0; i < sY.size(); ++i)
      if (sY[i] > tY)
        ++rY;
    const Index r = std::max<Index>(1, std::min(rX, rY)); // ensure >=1

    // Truncate U to ranks
    const Mat Ux = svdX.matrixU().leftCols(rX); // n x rX
    const Mat Uy = svdY.matrixU().leftCols(rY); // n x rY

    // 3) CCA via SVD on Ux^T Uy
    //    M is rX x rY => SVD: L (rX x r), Σ (r x r), R (rY x r)
    const Mat M = Ux.transpose() * Uy;
    Eigen::JacobiSVD<Mat> svdM(M, Eigen::ComputeThinU | Eigen::ComputeThinV);
    const Mat L = svdM.matrixU().leftCols(r);      // rX x r
    const Vec sig = svdM.singularValues().head(r); // canonical correlations (length r)
    const Mat R = svdM.matrixV().leftCols(r);      // rY x r

    // 4) Sample-space canonical variates for X: UxQx = Ux * L  (n x r)
    const Mat UxQx = Ux * L;

    // 5) Projection coefficients of neurons (columns of Xc) onto UxQx
    //    C = (UxQx)^T * Xc  (r x p)
    const Mat C = UxQx.transpose() * Xc;

    // 6) Weights: rowwise sum of absolute coefficients, then normalize
    Vec w = Vec::Zero(r);
    for (Index i = 0; i < r; ++i)
    {
      w[i] = C.row(i).cwiseAbs().sum();
    }
    double wsum = w.sum();
    if (wsum <= 0.0 || !std::isfinite(wsum))
    {
      // fallback: uniform weights
      w.setOnes();
      wsum = static_cast<double>(r);
    }
    w.array() /= wsum;

    // 7) Weighted sum of canonical correlations
    double pwcca = 0.0;
    for (Index i = 0; i < r; ++i)
    {
      // guard for numerical leakage of corr > 1
      const double rho = std::min(1.0, std::max(0.0, sig[i]));
      pwcca += w[i] * rho;
    }
    return pwcca;
  }

  // Batched PWCCA over a vector of matrices (same n rows each)
  inline Mat core_PWCCA(const std::vector<Mat> &Xs)
  {
    const Index M = static_cast<Index>(Xs.size());
    Mat out = Mat::Zero(M, M);
    // Diagonals = 1 by convention (similarity with itself)
    out.diagonal().setOnes();

    for (Index i = 0; i < M; ++i)
    {
      for (Index j = i + 1; j < M; ++j)
      {
        const double sij = core_PWCCA_pair(Xs[i], Xs[j]);
        // PWCCA is symmetric (if you always weight from the same side,
        // you *can* get asymmetry; common convention is X->Y weights.
        // Here we symmetrize by averaging both directions.)
        const double sji = core_PWCCA_pair(Xs[j], Xs[i]);
        const double s = 0.5 * (sij + sji);
        out(i, j) = s;
        out(j, i) = s;
      }
    }
    return out;
  }
} // namespace