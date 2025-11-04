#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime as dt
import xarray as xr
import cdsapi
from tqdm.auto import tqdm


class ERA5():
    def __init__(self, cdsapi_key, url='https://cds.climate.copernicus.eu/api'):
        """Convenience class for downloading and processing ECMWF
        ERA5 SST reanalysis data.

        Parameters
        ----------
        cdsapi_key : str
            Copernicus CDSAPI key.
        url : str, optional
            URL of Copernicus Data Store.
        """

        self.this_year = dt.datetime.now().year
        self.this_month = dt.datetime.now().month

        # Need a Copernicus Data Store (CDS) API key (formerly beta during 2024)
        self.c = cdsapi.Client(key=cdsapi_key, url=url)

    def _get_era5_monthly_means(self, outpath, year, month=None):
        """Retrieve ERA5 reanalyis *monthly means* in grib format.
        """

        if month is None:
            fname = f'sst_{year}.grib'
            months = [str(m) for m in range(1, 13)]
        else:
            fname = f'sst_{year}_{month:02}.grib'

        self.c.retrieve('reanalysis-era5-single-levels-monthly-means',
                        {'product_type': 'monthly_averaged_reanalysis',
                         'format': 'grib',
                         'variable': 'sea_surface_temperature',
                         'year': str(year),
                         'month': months if month is None else f'{month:02}',
                         'time': '00:00'}
                       ).download(os.path.join(outpath, fname))

    def download(self, outpath, year_range=(None, None), months=None,
                 overwrite=False, skip_error=False):
        """Download ERA5 data on single levels for a single variable.

        Parameters
        ----------
            outpath : str
                Output path to save files.
            year_range : (int, int), optional
                Year range to download.
            months : list, optional
                List of months to download. Defaults to full year.
            overwrite : boolean, optional
                If True, don't check for existence of file before downloading.
                Defaults to False.
            skip_error : boolean, optional
                If True, skips any download errors via try-except.
                Defaults to True.
        """

        years = range(year_range[0], year_range[1]+1)
        if months is None:
            months = range(1,13)

            # Loop over years
            for year in years:
                fname = f'sst_{year}.grib'
                if not overwrite and os.path.exists(os.path.join(outpath, fname)):
                    print(f'Skipping {fname} as it exists in directory.')
                else:
                    if skip_error:
                        try:
                            self._get_era5_monthly_means(outpath, year)
                        except:
                            print(f'*** FAILED {year} ***')
                    else:
                        self._get_era5_monthly_means(outpath, year)
        else:
            # Loop over years and months
            for year in years:
                for month in months:
                    fname = f'sst_{year}_{month:02}.grib'
                    if not overwrite and os.path.exists(os.path.join(outpath, fname)):
                        print(f'Skipping {fname} as it exists in directory.')
                    else:
                        if skip_error:
                            try:
                                self._get_era5_monthly_means(outpath, year, month)
                            except:
                                print(f'*** FAILED {year}-{month:02} ***')
                        else:
                            self._get_era5_monthly_means(outpath, year, month)

    def convert(self, da):
        """Convert units and structure of raw files.

        Unit conversion for SST is Kelvin => Celsius.

        Parameters
        ----------
            da : DataArray
                DataArray including dims ['time','latitude','longitude'].

        Returns
        -------
            da : DataArray
                Converted DataArray.
        """

        # Drop unneeded dims/coords
        da = da.drop(['number','step','surface','valid_time'])

        # Convert longitudes from 0->360 to -180->180
        da['longitude'] = ((da['longitude'] + 180) % 360) - 180
        da = da.sortby(['latitude','longitude'])

        # Temperature conversion from Kelvin to Celsius
        K_to_C = -273.15
        da = da + K_to_C

        # Convert time index to (year, month)
        da = da.assign_coords(year=('time', da.time.dt.year.data),
                              month=('time', da.time.dt.month.data)
                              ).set_index(time=('year', 'month')).unstack('time')
        return da

    def load(self, inpath, year_range=(None, None)):
        """Load and convert multiple ERA5 SST files.

        Parameters
        ----------
            inpath : str
                Path to ERA5 grib files.
            year_range : (int, int), optional
                Year range to process.

        Returns
        -------
            da : DataArray
                Processed DataArray.
        """

        year_from, year_to = year_range
        if year_from is None:
            year_from = 1940
        if year_to is None:
            year_to = self.this_year
        years = range(year_from, year_to+1)

        # Generate all file paths - assumes either yearly or monthly files
        fnames = [fname for fname in os.listdir(inpath)
                  if 'sst' in fname and 'grib' in fname and 'idx' not in fname]

        # Check if all years requested are available in fnames
        years_fnames = [int(fname.split('_')[1][:4]) for fname in fnames]
        years_missing = sorted(set(years) - set(years_fnames))
        if len(years_missing) > 0:
            print(f'Warning: some years in year_range not in {inpath}:\n'
                  f'{", ".join(map(str, years_missing))}')

        # Filename template sst_{year}.grib or sst_{year}_{month}.grib
        fpaths = [os.path.join(inpath, fname) for fname in sorted(fnames)
                  if int(fname.split('_')[1][:4]) in years]

        # Generate combined DataArray for all months for this variable
        da = [self.convert(xr.open_dataset(fpath, engine='cfgrib',
                                           backend_kwargs={'indexpath':''})['sst'])
                                           for fpath in tqdm(fpaths)]
        return xr.combine_by_coords(da)['sst']


# If running from the command line, only download a single month's data
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Arguments: <outpath> <cdsapi_key> [<year> <month>]')
    else:
        # Always assume that outpath and cdsapi_key will be passed
        outpath, cdsapi_key = sys.argv[1], sys.argv[2]

        era5 = ERA5(cdsapi_key)

        if len(sys.argv) == 3: # No year or month passed - download *last* month
            year, month = era5.this_year, (era5.this_month - 1 ) % 12 + 1
        else:
            year, month = int(sys.argv[3]), int(sys.argv[4])

        era5.download(outpath, year_range=(year, year), months=[month],
                    overwrite=False, skip_error=True)
