#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime as dt
import pandas as pd
import xarray as xr
import cdsapi
from tqdm.auto import tqdm


class SEAS5():
    def __init__(self, cdsapi_key, url='https://cds.climate.copernicus.eu/api'):
        """Convenience class for downloading and processing ECMWF SEAS5
        seasonal forecast SST data.

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

    def _get_seas51_month(self, year, month, outpath):
        """Function to retrieve seasonal surface forecasts at monthly
        resolution from ECMWF SEAS5 system in grib format.
        """

        fname = f'sst_{year}_{month:02}.grib'
        self.c.retrieve('seasonal-monthly-single-levels',
                        {'format': 'grib',
                         'originating_centre': 'ecmwf',
                         'system': '51',
                         'variable': 'sea_surface_temperature',
                         'product_type': 'monthly_mean',
                         'year': year,
                         'month': month,
                         'leadtime_month': [1,2,3,4,5,6]}
                       ).download(os.path.join(outpath, fname))

    def download(self, outpath, year_range=(None, None), months=None,
                 overwrite=False, skip_error=False):
        """Download SEAS5 hindcast (1981-2016) or operational (2017-present)
        seasonal monthly statistics on single levels for a single variable.

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

        year_from, year_to = year_range
        if year_from is None:
            year_from = 1981
        if year_to is None:
            year_to = self.this_year
        years = range(year_from, year_to+1)

        if months is None:
            months = range(1, 13)

        # Loop over years and months
        for year in years:
            for month in months:
                fname = f'sst_{year}_{month:02}.grib'
                if not overwrite and os.path.exists(os.path.join(outpath, fname)):
                    print(f'Skipping {fname} as it exists in directory.')
                else:
                    if skip_error:
                        try:
                            self._get_seas51_month(year, month, outpath)
                        except:
                            print(f'*** FAILED {year}-{month:02} ***')
                    else:
                        self._get_seas51_month(year, month, outpath)

    def convert(self, da):
        """Convert units and structure of raw files.

        Unit conversion for SST is Kelvin => Celsius.

        Parameters
        ----------
            da : DataArray
                DataArray with dims ['number','step','latitude','longitude'].

        Returns
        -------
            da : DataArray
                Converted DataArray.
        """

        # Sense check that only a single month is being used
        if da.time.ndim > 0:
            print('Dataset has more than one forecast date'
                ' - ensure file has a single forecast date only.')
            return None

        # Convert times and offsets to effective dates
        eff_date = da.time.values + da.step.values
        da = da.drop(['surface','valid_time','time']
                     ).assign_coords({'step': eff_date}
                                     ).rename({'step': 'time'})

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

        # Make number 1-indexed
        da['number'] = da['number'] + 1

        return da.to_dataset(dim='number')

    def load(self, inpath, month, year_range=(None, None)):
        """Load and convert multiple SEAS5 SST forecast files.

        Process forecast data on single levels for a single forecast month.
        Assumes standard SEAS5 raw grib file structure with dimensions
        [number, step, latitude, longitude] and a simple filename convention,
        and converts to a DataArray with dimensions of [number, year, month,
        latitude, longitude].

        Parameters
        ----------
            inpath : str
                Path to SEAS5 grib files.
            month : int
                Forecast month.
            year_range : (int, int), optional
                Year range to process.

        Returns
        -------
            da : DataArray
                Processed DataArray.
        """

        year_from, year_to = year_range
        if year_from is None:
            year_from = 1981
        if year_to is None:
            year_to = self.this_year
        years = range(year_from, year_to+1)

        # Generate all file paths - assumes either yearly or monthly files
        fnames = [f'sst_{year}_{month:02}.grib' for year in years]

        # Check if all years requested are available in fnames
        years_fnames = [int(fname.split('_')[1][:4]) for fname in fnames]
        years_missing = sorted(set(years) - set(years_fnames))
        if len(years_missing) > 0:
            print(f'Warning: some years in year_range not in {inpath}:\n'
                  f'{", ".join(map(str, years_missing))}')

        # Filename template sst_{year}_{month}.grib
        fpaths = [os.path.join(inpath, fname) for fname in sorted(fnames)
                  if int(fname.split('_')[1][:4]) in years]

        # Generate combined DataArray for all months for this variable
        return xr.merge([self.convert(xr.open_dataset(fpath, engine='cfgrib',
                                                      filter_by_keys={'dataType': 'fcmean'},
                                                      backend_kwargs={'indexpath':''})['sst'])
                                                      for fpath in tqdm(fpaths)]
                                                      ).expand_dims({'fmonth': [month]})


# If running from the command line, only download a single month's forecast
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Arguments: <outpath> <cdsapi_key> [<year> <month>]')
    else:
        # Always assume that cdsapi_key and outpath will be passed
        cdsapi_key, outpath = sys.argv[1], sys.argv[2]
        seas5 = SEAS5(cdsapi_key)

        if len(sys.argv) == 3: # No year or month passed
            year, month = seas5.this_year, seas5.this_month
        else:
            year, month = int(sys.argv[3]), int(sys.argv[4])

        seas5.download(outpath, year_range=(year, year), months=[month],
                    overwrite=False, skip_error=False)
