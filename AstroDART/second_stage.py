#%%
import os as os
import glob as glob
import numpy as np
from astropy.io import fits
from tqdm import tqdm
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
from astropy.table import Table
from astroquery.astrometry_net import AstrometryNet
from astropy.wcs import WCS
from .utils import *
from astropy.coordinates import SkyCoord
import matplotlib.pyplot as plt
from astropy.visualization import ZScaleInterval
z = ZScaleInterval()


class check_ds9:

    def __init__(self,image) -> None:
        self.image = image

    def run(self) -> None:
        
        ccd_data  = save_and_load_data(load_name=self.image).load_ccddata_from_fits().data
        z1_all,z2_all = z.get_limits(ccd_data)
        fig = plt.figure(figsize=(10,5))
        ax1 = fig.add_subplot()
        img = ax1.imshow(ccd_data, interpolation='nearest', cmap='magma',vmin=z1_all, vmax=z2_all)
        cbar = plt.colorbar(img, ax=ax1)
        cbar.set_label('Z scaled flux $\mathrm{[e^{-1}]}$')



class get_fwhm:

    def __init__(self, files) -> None:
        self.files = files
    
    def estimate_fwhm(self) -> list:
        _sources_ = [] 
        print('Finding sources')
        for ii in tqdm(range(len(self.files))):
            data = save_and_load_data(load_name=self.files[ii]).load_ccddata_from_fits().data

            mean, median, std = sigma_clipped_stats(data, sigma=3.0)
            daofind = DAOStarFinder(fwhm=3.0, threshold=5.0 * std)
            sources = daofind(data - median)
            
            _sources_.append(sources)
        
        self.sources = _sources_
        
        fwhm = []
        fwhms = []
        print('Estimating fwhms')
        for ii in tqdm(range(len(self.sources))):
            data = save_and_load_data(load_name=self.files[ii]).load_ccddata_from_fits().data
            for source in self.sources[ii]:
                x, y = int(source['xcentroid']), int(source['ycentroid'])
        
                x_min, x_max = max(x - 10, 0), min(x + 10, data.shape[1])
                y_min, y_max = max(y - 10, 0), min(y + 10, data.shape[0])
                
                sub_data = data[y_min:y_max, x_min:x_max]
                
                if sub_data.size == 0:
                    print(f"Skipping star at ({x}, {y}) - empty sub_data")
                    continue
                
                max_val = np.max(sub_data)
                half_max = max_val / 2.0
                y_indices, x_indices = np.where(sub_data >= half_max)
                
                if len(x_indices) > 0:
                    fwhm_x = np.max(x_indices) - np.min(x_indices)
                    fwhm_y = np.max(y_indices) - np.min(y_indices)
                    fwhms.append((fwhm_x, fwhm_y))
                else:
                    print(f"Skipping star at ({x}, {y}) - no half-max pixels")
            
            fwhm.append(np.mean(fwhms))
        
        return np.array(fwhm)





class astrometry:

    def __init__(self, directory: str ,files: list[str], api_key: str, fwhm: float) -> None:
        self.directory = directory
        self.files = files
        self.api_key = api_key
        self.astrometry_results = []
        self.fwhm = fwhm

    def run(self) -> None:
        wcs_list = []
        failed_astrometry_files = []

        for ii in tqdm(range(len(self.files))):
            try:
                print('Currently doing astrometry on:' + self.files[ii])
                
                data = save_and_load_data(load_name=self.files[ii]).load_ccddata_from_fits()
                scale = data.header['SCALE']
                ra = data.header['RA'].replace(' ',':')
                dec = data.header['DEC'].replace(' ',':')
                data = data.data
                

                coords_string = ra + ' ' + dec

                _c_ = SkyCoord(coords_string, unit=(u.hourangle, u.deg))
                
                mean , median, std = sigma_clipped_stats(data,sigma=3.0)
                

                ra_deg = _c_.ra.deg
                dec_deg = _c_.dec.deg

                
                daofind = DAOStarFinder(fwhm=self.fwhm[ii]*scale, threshold=5*std)  
                sources = daofind(data - median)  
                
                for col in sources.colnames:  
                    if col not in ('id', 'npix'):
                        sources[col].info.format = '%.2f'  
                sources.pprint(max_width=76)
                
                
                
                table_data = Table(sources)
                
                
                ecsv_file =  self.directory + 'values' + str(ii) + '.ecsv'
                table_data.write(ecsv_file, overwrite=True) 
                
                
                ast = AstrometryNet()
                ast.api_key = self.api_key
                
                
                
                sources = Table.read(ecsv_file)
                
                # Sort sources in ascending order
                sources.sort('flux')
                # Reverse to get descending order
                sources.reverse()
                
                image_width = data.shape[0]
                image_height = data.shape[-1]
                

                radius_in_degrees =  image_width*scale/3600
                wcs_header = ast.solve_from_source_list(sources['xcentroid'], sources['ycentroid'],
                                                        image_width, image_height,
                                                        solve_timeout=360,center_ra=ra_deg, 
                                                        center_dec=dec_deg, radius=radius_in_degrees)
                
                
                _wcs_ = WCS(wcs_header)
                wcs_list.append(_wcs_)
                
                with fits.open(self.files[ii], mode="update") as hdul:
                    
                    hdul[0].header.update(_wcs_.to_header())
                    hdul.flush()
                os.remove(ecsv_file)

            except:
                print(f'Astrometry failed on file {self.files[ii]}')
                failed_astrometry_files.append(self.files[ii])
                pass
            else:
                pass

        return failed_astrometry_files




# %%
