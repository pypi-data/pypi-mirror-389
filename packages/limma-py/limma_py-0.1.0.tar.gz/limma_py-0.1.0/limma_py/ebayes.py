import numpy as np
import pandas as pd
from scipy.stats import f
from scipy.stats import t
from .test_functions import classify_tests_f
from .squeezeVar import squeezeVar

def eBayes(fit,proportion=0.01,stdev_coef_lim=(0.1,4),trend=False,robust=False,winsor_tail_p=(0.05,0.1),legacy=None):
    """
    Empirical Bayes moderation of standard errors for linear model fits.

    Moderates the standard errors by borrowing information across genes using
    empirical Bayes methods. This improves statistical inference for differential
    expression analysis, especially useful for datasets with many genes but few samples.

    Parameters
    ----------
    fit : dict
        Dictionary containing linear model fitting results from lmFit.
        Required keys:
        - coefficients: Coefficient matrix
        - stdev_unscaled: Unscaled standard errors matrix
        - sigma: Residual standard deviations
        - df_residual: Residual degrees of freedom

    proportion : float, optional
        Prior proportion of genes expected to be differentially expressed.
        Default: 0.01

    stdev_coef_lim : tuple, optional
        Limits for the ratio of prior to posterior standard deviations.
        Default: (0.1, 4)

    trend : bool or array-like, optional
        Whether to account for trend in variances with expression level.
        If True, uses Amean as covariate. If array, uses as trend covariate.
        Default: False

    robust : bool, optional
        Whether to use robust estimation methods. Default: False

    winsor_tail_p : tuple, optional
        Tail probabilities for Winsorization in robust estimation.
        Default: (0.05, 0.1)

    legacy : bool, optional
        Whether to use legacy method for handling unequal degrees of freedom.
        Default: None (automatically determined)

    Returns
    -------
    dict
        Updated fit dictionary with additional empirical Bayes results:
        - df_prior: Prior degrees of freedom
        - s2_prior: Prior variance
        - s2_post: Posterior variance
        - var_prior: Prior variance for coefficients
        - t: Moderated t-statistics
        - df_total: Total degrees of freedom
        - p_value: Moderated p-values
        - lods: Log-odds of differential expression
        - F: F-statistics (if design permits)
        - F_p_value: F-test p-values (if design permits)

    Examples
    --------
    >>> import limma_py as limma
    >>> import numpy as np
    >>> import pandas as pd

    # Create example data (100 genes, 6 samples)
    >>> expr_data = pd.DataFrame(np.random.randn(100, 6))
    >>> design = pd.DataFrame({'Group1': [1,1,1,0,0,0], 'Group2': [0,0,0,1,1,1]})

    # Linear model fitting
    >>> fit = limma.lmFit(expr_data, design)

    # Empirical Bayes moderation
    >>> eb_fit = limma.eBayes(fit)

    # Check results
    >>> print("Keys in eBayes output:", list(eb_fit.keys()))
    >>> print("Moderated t-statistics shape:", eb_fit['t'].shape)
    >>> print("Prior degrees of freedom:", eb_fit['df_prior'])

    Notes
    -----
    - Empirical Bayes moderation shrinks extreme variances toward the common trend.
    - The method is particularly powerful for small sample sizes.
    - Setting trend=True can improve performance when variance depends on expression level.
    - Robust estimation provides protection against outlier genes.

    References
    ----------
    Smyth, G. K. (2004). Linear models and empirical bayes methods for
    assessing differential expression in microarray experiments.
    Statistical Applications in Genetics and Molecular Biology, 3(1), Article 3.
    """
    if not isinstance(fit, dict): 
        raise TypeError("fit is not a valid dict object")

    if trend is True and fit.get("Amean") is None:
        raise ValueError("Need Amean component in fit to estimate trend")

    # 假设 _ebayes 返回一个字典 eb
    eb = _ebayes(
        fit=fit,
        proportion=proportion,
        stdev_coef_lim=stdev_coef_lim,
        trend=trend,
        robust=robust,
        winsor_tail_p=winsor_tail_p,
        legacy=legacy,
    )
    # 把 eb 里的字段回填到 fit
    fit.update({
        "df_prior": eb["df_prior"],
        "s2_prior": eb["s2_prior"],
        "var_prior": eb["var_prior"],
        "proportion": proportion,
        "s2_post": eb["s2_post"],
        "t": eb["t"],
        "df_total": eb["df_total"],
        "p_value": eb["p_value"],
        "lods": eb["lods"],
    })
    # 在 ebayes.py 中替换
    if fit.get("design") is not None and np.linalg.matrix_rank(fit["design"]) == fit["design"].shape[1]:
        F_stat = classify_tests_f(fit, fstat_only=True)  # 调用 classify_tests_f，只返回 F 统计量
        fit["F"] = F_stat.to_numpy().ravel()  # 将 F 统计量转换为一维数组
        df1 = F_stat.attrs["df1"]  # 获取分子自由度
        df2 = F_stat.attrs["df2"]  # 获取分母自由度
        fit["F_p_value"] = f.sf(fit["F"], df1, df2)  # 计算 F 统计量的 p 值
    return fit

def _ebayes(fit, proportion, stdev_coef_lim, trend, robust, winsor_tail_p, legacy):
    coefficients = fit["coefficients"]
    stdev_unscaled = fit["stdev_unscaled"]
    sigma = fit["sigma"]
    df_residual = fit["df_residual"]

    if (coefficients is None or
            stdev_unscaled is None or
            sigma is None or
            df_residual is None):
        raise ValueError("No data, or argument is not a valid lmFit object")

    if np.max(df_residual) == 0:
        raise ValueError("No residual degrees of freedom in linear model fits")

    if not np.any(np.isfinite(sigma)):
        raise ValueError("No finite residual standard deviations")

    sigma = fit["sigma"]

    if isinstance(trend, bool):
        if trend:
            covariate = fit.get("Amean")
            if covariate is None:
                raise ValueError("Need Amean component in fit to estimate trend")
        else:
            covariate = None
    elif isinstance(trend, (list, np.ndarray, pd.Series)):
        if len(trend) != len(sigma):
            raise ValueError("If trend is numeric then it should have length equal to the number of genes")
        covariate = trend
    else:
        raise ValueError("trend should be either a logical scale or a numeric vector")

    out = squeezeVar(sigma ** 2, df_residual, covariate=covariate, robust=robust, winsor_tail_p=winsor_tail_p, legacy=legacy)

    out["s2_prior"] = out["var_prior"]
    out["s2_post"] = out["var_post"]
    del out["var_prior"]
    del out["var_post"]

    # 1. 确保 s2_post 是形状为 (基因数, 1) 的二维数组
    s2_post = out["s2_post"].reshape(-1, 1)  # 关键：转换为列向量

    # 2. 将 coefficients 和 stdev_unscaled 转换为 numpy 数组（移除 pandas 索引影响）
    coef_np = coefficients
    stdev_np = np.asarray(stdev_unscaled)

    # 3. 执行除法运算（此时形状兼容：[n×4] / [n×4] / [n×1]）
    out["t"] = coef_np / stdev_np / np.sqrt(s2_post)
    # 计算 df.total
    df_total = df_residual + out["df_prior"]

    # 计算 df.pooled（忽略 NaN 值）
    df_pooled = np.sum(df_residual, axis=0)

    # 确保 df.total 不超过 df.pooled
    df_total = np.minimum(df_total, df_pooled)

    out["df_total"] = df_total

    df_total_2d = np.asarray(out["df_total"])[:, np.newaxis]
    out["p_value"] = 2 * t.sf(np.abs(out["t"]), df=df_total_2d)

    stdev_coef_lim_sq = np.square(stdev_coef_lim)
    var_prior_lim = stdev_coef_lim_sq / np.median(out["s2_prior"])
    # 在调用 tmixture_matrix 之前添加调试

    out["var_prior"] = tmixture_matrix(out["t"], stdev_unscaled, out["df_total"], proportion, var_prior_lim)

    if np.any(np.isnan(out["var_prior"])):
        # 将 NaN 值替换为 1 / s2_prior
        out["var_prior"][np.isnan(out["var_prior"])] = 1 / out["s2_prior"]
        # 发出警告
        import warnings
        warnings.warn("Estimation of var.prior failed - set to default value")

    r = np.zeros_like(stdev_np)
    for j in range(stdev_np.shape[1]):
        r[:, j] = (stdev_np[:, j] ** 2 + out["var_prior"][j]) / stdev_np[:, j] ** 2

    t2 = np.asarray(out["t"]) **2

    Infdf = out["df_prior"] > 10 ** 6
    if np.any(Infdf):
        kernel = t2 * (1 - 1 / r) / 2
        if np.any(~Infdf):
            t2_f = t2[~Infdf]
            r_f = r[~Infdf]
            df_total_f = out["df_total"][~Infdf]
            kernel[~Infdf] = (1 + df_total_f) / 2 * np.log((t2_f + df_total_f) / (t2_f / r_f + df_total_f))
    else:
        df_total = out["df_total"]
        df_total_2d = df_total.reshape(-1, 1)
        kernel = (1 + df_total_2d) / 2 * np.log((t2 + df_total_2d) / (t2 / r + df_total_2d))

    out["lods"] = np.log(proportion / (1 - proportion)) - np.log(r) / 2 + kernel

    return out


def tmixture_matrix(tstat, stdev_unscaled, df, proportion, v0_lim=None):
    # 确保输入是二维数组
    tstat = np.atleast_2d(tstat)
    stdev_unscaled = np.atleast_2d(stdev_unscaled)

    if tstat.shape != stdev_unscaled.shape:
        raise ValueError("Dims of tstat and stdev.unscaled don't match")

    if v0_lim is not None and len(v0_lim) != 2:
        raise ValueError("v0_lim must have length 2")

    ncoef = tstat.shape[1]
    v0 = np.zeros(ncoef)

    # 为每个系数列计算 var.prior
    for j in range(ncoef):

        v0[j] = tmixture_vector(tstat[:, j], stdev_unscaled[:, j], df, proportion, v0_lim)


    return v0


def tmixture_vector(tstat, stdev_unscaled, df, proportion, v0_lim=None):
    # 关键修正：确保所有输入都是一维数组
    tstat = np.asarray(tstat).flatten()
    stdev_unscaled = np.asarray(stdev_unscaled).flatten()
    df = np.asarray(df).flatten()

    # Step 1: 去除缺失值
    if np.any(np.isnan(tstat)):
        o = ~np.isnan(tstat)
        tstat = tstat[o]
        stdev_unscaled = stdev_unscaled[o]
        df = df[o]

    # Step 2: 选取目标数量
    ngenes = len(tstat)
    ntarget = int(np.ceil(proportion / 2 * ngenes))
    if ntarget < 1:
        return np.nan

    p = max(ntarget / ngenes, proportion)

    # Step 3: 统一自由度
    tstat_abs = np.abs(tstat)
    MaxDF = np.max(df)
    i = df < MaxDF
    if np.any(i):
        TailP = t.logsf(tstat_abs[i], df[i])
        tstat_abs[i] = t.ppf(1 - np.exp(TailP), MaxDF)
        df[i] = MaxDF

    # Step 4: 选取最显著的ntarget个t
    o = np.argsort(-tstat_abs)[:ntarget]
    tstat_selected = tstat_abs[o]
    v1 = stdev_unscaled[o] ** 2

    # Step 5: 计算p0和ptarget
    p0 = 2 * t.sf(tstat_selected, df=MaxDF)
    r = np.arange(1, ntarget + 1)
    ptarget = ((r - 0.5) / ngenes - (1 - p) * p0) / p
    ptarget = np.maximum(ptarget, 1e-10)

    # Step 6: 根据显著性反推v0
    v0 = np.zeros(ntarget)
    pos = ptarget > p0
    if np.any(pos):
        qtarget = t.ppf(1 - ptarget[pos] / 2, df=MaxDF)
        v0[pos] = v1[pos] * ((tstat_selected[pos] / qtarget) ** 2 - 1)

    # Step 7: 限制v0范围
    if v0_lim is not None:
        v0 = np.clip(v0, v0_lim[0], v0_lim[1])

    # Step 8: 平均返回
    valid_v0 = v0[np.isfinite(v0)]
    if len(valid_v0) == 0:
        return np.nan

    v0_mean = np.mean(valid_v0)
    return v0_mean
