#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import json
import numpy as np
import scipy.spatial as sp
import pandas as pd
import xarray as xr
from tqdm.auto import tqdm

# Sub-modules for working with SST data
from .ersst5 import ERSST5
from .era5 import ERA5
from .seas5 import SEAS5


class TeleSST():
    def __init__(self, source, tqdm=False):
        """Class constructor to generate teleconnection features from SSTs.

        Parameters
        ----------
            source : str
                Source dataset - must be ERSSTv5, ERA5 or SEAS5.
            tqdm : bool, optional
                Show tqdm progress bars. Defaults to False.
        """

        if source.lower() in ['ersstv5','era5','seas5']:
            self.source = source
        else:
            print('source must be ERSSTv5, ERA5 or SEAS5')
            return None

        self.tqdm = not tqdm

        # List available precomputed climatologies for calculating anomalies
        self.climpath = os.path.join(os.path.dirname(__file__), 'clims', source)

        # Update available climatologies
        self.clims_available = sorted([f'{clim.split(".")[0]}'
                                       for clim in os.listdir(self.climpath)
                                       if 'zarr' in clim and not clim.startswith('.')])
        self.clim = None

        self.now = datetime.datetime.now()
        self.EOFs, self.PCs = None, None
        self.meta = {'source': self.source,
                     'year_range': None,
                     'lat_range': None,
                     'weighting': None,
                     'clims': None}

    def download(self, outpath, year_range=(None,None), months=None,
                 overwrite=False, skip_error=False, cdsapi_key=None, proxy={}):
        """Download SST data from ERSSTv5, ERA5 or SEAS5.

        Parameters
        ----------
            outpath : str
                Output path to save files.
            year_range : (int, int), optional
                Year range to download. Defaults to maximum possible range.
            months : list, optional
                List of months to download. Defaults to full year.
            overwrite : boolean, optional
                If True, don't check for existence of file before downloading.
                Defaults to False.
            skip_error : boolean, optional
                If True, skips any download errors via try-except.
                Defaults to True.
            cdsapi_key : str, optional
                Copernicus Data Store Beta (CDS-Beta) API key if downloading
                ERA5 or SEAS5 data.
            proxy : dict, optional
                Proxy dictionary if needed for ERSSTv5.
        """

        # Load the raw data
        if self.source.lower() == 'ersstv5':
            ersst5 = ERSST5()
            ersst5.download(outpath, year_range=year_range, months=months,
                            overwrite=overwrite, proxy=proxy)
        elif self.source.lower() == 'era5':
            era5 = ERA5(cdsapi_key=cdsapi_key)
            era5.download(outpath, year_range=year_range, months=months,
                          overwrite=overwrite, skip_error=skip_error)
        else: # SEAS5
            seas5 = SEAS5(cdsapi_key=cdsapi_key)
            seas5.download(outpath, year_range=year_range, months=months,
                           overwrite=overwrite, skip_error=skip_error)

    def load(self, inpath, year_range=(None, None), fmonth=None):
        """Load raw SST data and convert to tabular structure.

        Parameters
        ----------
            inpath : str
                Path to raw SST data.
            year_range : (int, int), optional
                Year range to process.
            fmonth : int, optional
                Forecast month - only for SEAS5.
        """

        # Load the raw data
        if self.source.lower() == 'ersstv5':
            ersst5 = ERSST5()
            return ersst5.load(inpath, year_range=year_range)
        elif self.source.lower() == 'era5':
            era5 = ERA5(cdsapi_key='dummy')
            return era5.load(inpath, year_range=year_range)
        else: # SEAS5
            if fmonth is None:
                print('fmonth must be specified for SEAS5 forecasts')
                return None
            seas5 = SEAS5(cdsapi_key='dummy')
            return seas5.load(inpath, year_range=year_range, month=fmonth)

    def calc_clim(self, da, clim_year_range):
        """Calculate a climatology for a single nominal year range.

        Takes the average over all grid locations and months over the
        year_range passed. Assumes time dimension converted to [year, month].

        Parameters
        ----------
            da : DataArray
                Converted DataArray of SSTs, or Dataset in the case of SEAS5.
            clim_year_range : (int, int)
                Year range over which to calculate climatology.

        Returns
        -------
            da : DataArray
                Climatology DataArray.
        """

        year_min, year_max = da['year'].values.min(), da['year'].values.max()

        # isinstance checks to handle December forecast year_min edge case
        if  year_min > clim_year_range[0] and isinstance(da, xr.DataArray):
            print(f'Smallest year in da is {year_min} > {clim_year_range[0]}')
            return None
        if year_min - 1 > clim_year_range[0] and isinstance(da, xr.Dataset):
            print(f'Smallest year in da is {year_min-1} > {clim_year_range[0]}')
            return None
        if year_max < clim_year_range[1]:
            print(f'Largest year in da is {year_max} < {clim_year_range[1]}')
            return None

        if isinstance(da, xr.DataArray): # ERA5 or ERSSTv5
            da_clim = da.sel(year=slice(*clim_year_range)).mean(dim='year')
        else: # SEAS5 forecast
            da_clim = da.sel(year=slice(*clim_year_range)
                             ).to_dataarray('number').mean(dim=['year','number'])

        return da_clim.assign_attrs(desc='SST climatology', source=f'{self.source}',
                                    clim_range=clim_year_range)

    def calc_clims(self, inpath, years_from, years_to):
        """Calculate multiple climatologies for all years in a year range.

        Calculates NOAA N-year centred climatologies in 5-year chunks and saves
        in self.climpath. Assumes the time dimension converted to [year, month].

        Parameters
        ----------
            inpath : str
                Path to monthly NetCDF files.
            years_from : iterable of ints
                'From' years to calculate climatologies.
            years_to : iterable of ints
                'To' years to calculate climatologies.
        """

        for year_from, year_to in zip(years_from, years_to):
            print(f'Processing {year_from}-{year_to}...', end=' ')
            if self.source.lower() in ['ersstv5','era5']:
                data = self.load(inpath, (year_from, year_to))
                clim = self.calc_clim(data, (year_from, year_to))
                out_fpath = os.path.join(self.climpath, f'sst_{year_from}_{year_to}.zarr')
                if clim is not None and not os.path.exists(out_fpath):
                    print('Writing to disk...')
                    clim.to_zarr(out_fpath)
            else: # SEAS5
                clim = []
                for fmonth in tqdm(range(1, 13), disable=self.tqdm):
                    data = self.load(inpath, (year_from, year_to), fmonth)
                    clim.append(self.calc_clim(data, (year_from, year_to)))
                clim = xr.concat(clim, dim='fmonth').rename('sst')
                out_fpath = os.path.join(self.climpath, f'sst_{year_from}_{year_to}.zarr')
                if not os.path.exists(out_fpath):
                    print('Writing to disk...')
                    clim.to_zarr(out_fpath)

        # Update available climatologies
        self.clims_available = sorted([f'{clim.split(".")[0]}'
                                       for clim in os.listdir(self.climpath)
                                       if 'zarr' in clim and not clim.startswith('.')])

    def load_clim(self, year_range):
        """Load precomputed climatology.

        Parameters
        ----------
            year_range : (int, int)
                Climatology year range to load.
        """

        fname =  f'sst_{year_range[0]}_{year_range[1]}.zarr'
        self.clim = xr.open_dataset(os.path.join(self.climpath, fname),
                                    engine='zarr')['sst']
        return self.clim

    def calc_anoms(self, da, clims):
        """Calculate anomalies from data and precomputed climatologies.

        Parameters
        ----------
            da : DataArray
                Converted DataArray of SSTs.
            clims : DataFrame
                DataFrame indexed by year with year_from and year_to columns,
                for calculating the climatologies for each year.

        Returns
        -------
            anoms : DataArray
                Processed anomalies.
        """

        # Check that all years in da have a climatology range defined in clims
        missing_clim_years = da.get_index('year').difference(clims.index)
        if missing_clim_years.size > 0:
            print(f'Years {", ".join(map(str, missing_clim_years))}'
                  ' in da not in clims index')
            return None

        # Update climate periods in metadata
        self.meta['clims'] = clims.reset_index().to_dict(orient='records')

        # Subset clims DataFrame to match years in da
        clims_ix = clims.reindex(da.get_index('year').intersection(clims.index))

        anoms = []
        if self.source.lower() == 'seas5':
            for year_range, df in clims_ix.groupby(['year_from','year_to']):
                anoms.append(da.sel(year=df.index) - self.load_clim(year_range))
            return xr.merge(anoms)
        else:
            for year_range, df in clims_ix.groupby(['year_from','year_to']):
                anoms.append(da.sel(year=df.index) - self.load_clim(year_range))
            return xr.combine_by_coords(anoms)['sst']

    def anoms_to_PCs(self, anoms, year_range=(None,), lat_range=(None,),
                     weighting='rootcoslat'):
        """Calculate EOFs and PCs of reference data at monthly resolution.

        Parameters
        ----------
            anoms : DataArray
                DataArray with dims ['latitude','longitude','year','month'].
            year_range : (int, int), optional
                Year range subset to use to calculate EOFs. Defaults to all years.
            lat_range : (float, float), optional
                Latitude range subset to use. Defaults to (-90, 90).
            weighting : str, optional
                Weighting to apply to cells before processing. Either
                  'rootcoslat' - sqrt(cosine(latitude)) [default] or
                  'coslat' - cosine(latitude)
        """

        # Zero-mean by month over all time
        self.anoms_mean = anoms.mean(dim='year')

        # Subset latitudes and subtract mean
        da = anoms.sel(latitude=slice(*lat_range)) - self.anoms_mean

        # Calculate weights
        if weighting == 'coslat':
            self.wts_da = np.cos(np.deg2rad(da['latitude']))
        elif weighting == 'rootcoslat':
            self.wts_da = np.sqrt(np.cos(np.deg2rad(da['latitude'])))
        else:
            self.wts_da = xr.DataArray(1)
        self.wts = self.wts_da.to_series()

        # Calculate EOFs and PCs for each month
        EOFs, PCs = {}, {}

        for m in tqdm(range(1, 13), disable=self.tqdm):
            da_month = da.sel(month=m) * self.wts_da
            X = da_month.to_series().dropna().unstack('year').dropna(how='any').T
            _, _, V = np.linalg.svd(X.loc[slice(*year_range)], full_matrices=False)
            EOFs[m] = pd.DataFrame(V, columns=X.columns)
            PCs[m] = X @ EOFs[m].T

            # Align EOFs of successive months for ease of interpretation
            if m > 1:
                cols = EOFs[m].columns.intersection(EOFs[m-1].columns)
                sgn = np.sign(np.diag(EOFs[m][cols] @ EOFs[m-1][cols].T))
                EOFs[m] = EOFs[m] * sgn[:,None]
                PCs[m] = PCs[m] * sgn[None,:]

        # Convert to DataFrames
        self.EOFs = pd.concat(EOFs, names=['month','pc'])
        self.PCs = pd.concat(PCs, names=['month']
                             ).reorder_levels(['year','month']
                                              ).sort_index().rename_axis('pc', axis=1)
        # Update metadata
        self.meta['year_range'] = (int(da['year'].min()), int(da['year'].max()))
        self.meta['lat_range'] = (float(da['latitude'].min()), float(da['latitude'].max()))
        self.meta['weighting'] = weighting

    def _ll_to_xyz(self, lons_deg, lats_deg):
        """Convert surface WGS84 geodetic coordinates to ECEF coordinates.

        Allows the use of k-d trees for efficient nearest neighbour lookup.

        Parameters
        ----------
            lons_deg : ndarray, Series or Index
                Array of longitudes in decimal degrees.
            lats_deg : ndarray, Series or Index
                Array of latitudes in decimal degrees.

        Returns
        -------
            X : ndarray
                2D ndarray with 3 (x, y, z) columns and same number of rows as
                as length of input arrays.
        """

        # Convert input longitudes and latitudes to radians
        lons, lats = np.deg2rad(lons_deg), np.deg2rad(lats_deg),

        # Equatorial radius, flattening factor and eccentricity**2 for WGS84 Model
        R = 6_378_137.0
        f = 1.0 / 298.257223563
        e2 = 1 - (1 - f)**2

        # Transform lon, lats at MSL to x,y,z
        N = R / np.sqrt(1 - e2 * np.sin(lats)**2)
        x = N * np.cos(lats) * np.cos(lons)
        y = N * np.cos(lats) * np.sin(lons)
        z = (1 - e2) * N * np.sin(lats)
        return np.stack((x, y, z)).T

    def project(self, da, forecast=True):
        """Project new data onto EOFs previously fitted to get new PCs.

        Parameters
        ----------
            da : DataArray
                DataArray to be projected including dims
                ['latitude','longitude','year','month'].
            forecast : bool
                Flag if da is a forecast or not. If true, makes standard
                assumptions about the structure of a processed SEAS5 forecast.

        Returns
        -------
            PCs_proj : DataFrame
                Projected PCs.
        """

        # Pre-processing for forecast data - convert ensemble variables to dim
        if forecast:
            da = da.to_dataarray(dim='number').squeeze(dim='fmonth')

        # Make xarray coordinates from EOFs lat, lons
        da_ix = xr.Coordinates.from_pandas_multiindex(self.EOFs.columns, 'latlon')

        # Identify lons and lats in EOF DataFrame and convert to Cartesian
        lons_EOFs = self.EOFs.columns.get_level_values('longitude').to_numpy()
        lats_EOFs = self.EOFs.columns.get_level_values('latitude').to_numpy()
        xyz_EOFs = self._ll_to_xyz(lons_EOFs, lats_EOFs)

        # Identify non-null lons and lats in DataArray to be projected
        das = da.stack(latlon=['latitude','longitude'])
        ll = ~das.isnull().all(dim=set(das.dims) - {'latlon'})
        latlon_proj = ll[ll].get_index('latlon')
        lons_proj = latlon_proj.get_level_values('longitude').to_numpy()
        lats_proj = latlon_proj.get_level_values('latitude').to_numpy()
        xyz_proj = self._ll_to_xyz(lons_proj, lats_proj)

        # Make k-d tree from xyz_proj and query nearest values to xyz_EOF coords
        _, i = sp.KDTree(xyz_proj).query(xyz_EOFs)
        mix = pd.MultiIndex.from_arrays([lats_proj[i], lons_proj[i]],
                                        names=['latitude','longitude'])
        da_nearest = das.sel(latlon=mix).assign_coords(da_ix).unstack('latlon')

        # Apply latitude weights
        da_wt = da_nearest * self.wts_da

        # Do projection onto EOFs
        PCs_proj = {}
        for m in da_wt['month'].values:
            da_wt_m = da_wt.sel(month=m).to_series().dropna().unstack(['latitude','longitude']).T
            PCs_proj[m] = self.EOFs.xs(m, level='month') @ da_wt_m
        PCs_proj = pd.concat(PCs_proj, names=['month']).unstack('month').T.dropna().sort_index()
        return PCs_proj

    def to_file(self, outpath, desc):
        """Save EOFs and PCs to disk.

        Parameters
        ----------
            outpath : str
                Output path.
            desc : str
                Description of model.
        """

        if not os.path.exists(os.path.join(outpath, desc)):
            os.makedirs(os.path.join(outpath, desc))

        with open(os.path.join(outpath, desc, 'meta.json'), 'w') as f:
            json.dump(self.meta, f)

        self.EOFs.to_parquet(os.path.join(outpath, desc, f'EOFs.parquet'))
        self.PCs.to_parquet(os.path.join(outpath, desc, f'PCs.parquet'))
        anoms_mean = self.anoms_mean.to_series().dropna().unstack('month')
        anoms_mean.to_parquet(os.path.join(outpath, desc, f'anoms_mean.parquet'))

    def from_file(self, inpath, desc):
        """Load model from disk.

        Parameters
        ----------
            inpath : str
                Input path.
            desc : str
                Description of model.
        """

        with open(os.path.join(inpath, desc, 'meta.json'), 'r') as f:
            self.meta = json.load(f)

        self.source = self.meta['source']
        self.EOFs = pd.read_parquet(os.path.join(inpath, desc, f'EOFs.parquet'))
        self.PCs = pd.read_parquet(os.path.join(inpath, desc, f'PCs.parquet'))
        anoms_mean = pd.read_parquet(os.path.join(inpath, desc, f'anoms_mean.parquet'))
        self.anoms_mean = anoms_mean.stack('month').to_xarray()

        # Calculate weights
        lats = self.EOFs.columns.unique(level='latitude').to_series()
        if self.meta['weighting'] == 'coslat':
            self.wts_ss = np.cos(np.deg2rad(lats))
        elif self.meta['weighting'] == 'rootcoslat':
            self.wts_ss = np.sqrt(np.cos(np.deg2rad(lats)))
        else:
            self.wts_ss = (lats/lats).fillna(1)
        self.wts_da = self.wts_ss.to_xarray()
