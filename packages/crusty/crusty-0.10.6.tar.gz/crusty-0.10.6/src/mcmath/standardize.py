import numpy as np
import pandas as pd
from pandera.typing import Series
from mcmath.distributions import distribution_fit, distribution_pdf, distribution_cdf

def index_weight(sxi: np.ndarray,
                 weigh_mid: float,
                 weigh_steep: float) -> np.ndarray:

    # Weight SXI with logistic function
    # 10.1175/JHM-D-22-0115.1
    # Calculate logistic weight and set 1 values to np.nan
    
    w = np.where((~np.isnan(sxi) & (sxi < 0)),
                 1 / (1 + (weigh_mid / sxi)**weigh_steep),
                 np.nan)

    return w

def standard_index(array: np.ndarray, 
                   time_index: pd.Series,
                   variable: str = 'var',
                   distribution: str = 'gamma',
                   rolling: bool = True,
                   reftime: tuple[pd.Timestamp, pd.Timestamp] | None = None,
                   deseasonalize: bool = True,
                   window: str = '365D', 
                   agg_method: str = 'sum',
                   plot_distributions: bool = False,
                   plot_out_dir: str = 'png/',
                   plot_sxi_ts: bool = False,
                   plot_hist_bins: int = 30,
                   plot_lw: float = 2.0) -> np.ndarray:

    if isinstance(array, list): array = array[0]

    if (distribution == 'gamma') and deseasonalize: 
                       
        print('\nDeseasonalize and gamma distribution')
        print('are not compatible...\n')

        raise NotImplementedError

    valid_start = time_index.iloc[0] + pd.Timedelta(window)

    series = pd.Series(array,
                       index=time_index)
    
    series.index = pd.DatetimeIndex(series.index)

    if deseasonalize:

        series_mean_year = series.groupby(series.index.dayofyear, 
                                          group_keys=False) \
                                          .mean().values
        
        mean_year_sub = lambda x: x - series_mean_year

        series_deseasonalized = series.groupby(series.index.year, 
                                               group_keys=False) \
                                               .apply(mean_year_sub)

        series = series_deseasonalized

    series_roll = series.rolling(window).agg(agg_method) if rolling else series

    ref_slice = slice(valid_start, None) if reftime is None else slice(reftime[0], reftime[1])

    series_roll_ref = series_roll.loc[ref_slice]
    
    series_roll_valid = series.loc[valid_start:]

    dummy_out = np.array([np.nan] * len(series_roll_ref)) 

    if ((distribution == 'gamma') and 
        (np.any(series_roll_ref < 0) or 
         np.all(series_roll_ref == 0))): return dummy_out

    if np.all(np.isnan(series_roll_ref)): return dummy_out

    if np.all(series_roll_ref == series_roll_ref.iloc[0]): return dummy_out

    if distribution == 'gaussian_kde':

        from mcmath.distributions import gauss_kde_pdf, gauss_kde_cdf

        pdf_xs, pdf_ys = gauss_kde_pdf(series_roll_ref)

        cdf_xs, cdf_ys = gauss_kde_cdf(series_roll_ref)

    else:

        parameter = distribution_fit(series_roll_ref.to_numpy(), 
                                     distribution=distribution)

        pdf_xs, pdf_ys = distribution_pdf(distribution=distribution,
                                          parameter=parameter)

        cdf_xs, cdf_ys = distribution_cdf(distribution=distribution,
                                          parameter=parameter)

    pdf_normal_xs, pdf_normal_ys = distribution_pdf()

    cdf_normal_xs, cdf_normal_ys = distribution_cdf()

    series_roll_cdf = np.interp(series_roll_valid, 
                                cdf_xs, 
                                cdf_ys)

    series_roll_sxi = np.interp(series_roll_cdf, 
                                cdf_normal_ys, 
                                cdf_normal_xs)

    str_deseasonalize = 'deseasonalized' if deseasonalize else ''

    file_out = '_'.join([f'{variable}',
                         f'{distribution}',
                         f'{window}',
                         f'{agg_method}',
                         f'{str_deseasonalize}'])

    #if plot_distributions: 

        #create_dirs(plot_out_dir)
        
    #     fig, ax = square(4, 4)
    #     init_dist(ax,pdf_xs, pdf_ys, xlabel = f'{window} {agg_method} {variable} [{unit}]', ylabel = 'Probability density')
    #     plot(ax, xs = pdf_xs, ys = pdf_ys, lw = plot_lw, zorder = 2)
    #     hist(ax, series_roll, bins = plot_hist_bins, zorder = 1)
    #     save_png(fig, f'{plot_out_dir}/PDF_{file_out}.png')

    #     fig, ax = square(4, 4)
    #     init_dist(ax, cdf_xs, cdf_ys, xlabel = f'{window} {agg_method} {variable} [{unit}]', ylabel = 'Cummulative probability density')
    #     plot(ax, xs = cdf_xs, ys = cdf_ys, lw = plot_lw, zorder = 2)
    #     save_png(fig, f'{plot_out_dir}/CDF_{file_out}.png')
    
    #     fig, ax = square(4, 4)
    #     init_dist(ax, pdf_normal_xs, pdf_normal_ys, xlabel = 'SXI', ylabel = 'Probability density')
    #     plot(ax, xs = pdf_normal_xs, ys = pdf_normal_ys, lw = plot_lw, zorder = 2)
    #     save_png(fig, f'{plot_out_dir}/pdf_norm.png')    

    #     fig, ax = square(4, 4)
    #     init_dist(ax, cdf_normal_xs, cdf_normal_ys, xlabel = 'SXI', ylabel = 'Cummulative probability density')
    #     plot(ax, xs = cdf_normal_xs, ys = cdf_normal_ys, lw = plot_lw, zorder = 2)
    #     save_png(fig, f'{plot_out_dir}/cdf_norm.png')

    # if plot_sxi_ts:
        
    #     create_dirs(plot_out_dir)

    #     fig, ax, cax = square_top_cax(fy = 4)
    #     init_ts_2(ax, time_index, array, xlabel = 'Time', ylabel = f'{variable} [{unit}]')
    #     plot(ax, xs = time_index, ys = array, colors = 'k', lw = plot_lw, zorder = 2)
    #     color_legend(cax, {variable: 0}, ['k', 'firebrick'])        
    #     save_png(fig, f'{plot_out_dir}/TS_{file_out}.png')

    #     if deseasonalize:

    #         fig, ax, cax = square_top_cax(fy = 4)
    #         init_ts_2(ax, time_index, series_deseasonalized, xlabel = 'Time', ylabel = f'{variable} [{unit}]')
    #         plot(ax, xs = time_index, ys = series_deseasonalized, colors = 'k', lw = plot_lw, zorder = 2)
    #         color_legend(cax, {variable: 0}, ['k', 'firebrick'])        
    #         save_png(fig, f'{plot_out_dir}/TS_ds_{file_out}.png')


    #     fig, ax, cax = square_top_cax(fy = 4)
    #     init_ts_2(ax, time_index, series_roll_sxi, xlabel = 'Time', ylabel = 'SXI [-]')
    #     plot(ax, xs = time_index_valid, ys = series_roll_sxi, lw = plot_lw, colors = 'firebrick', zorder = 2)
    #     color_legend(cax, {f'{variable} Standardized Index': 1}, ['k', 'firebrick'])        
    #     save_png(fig, f'{plot_out_dir}/SXI_{file_out}.png')

    return series_roll_sxi