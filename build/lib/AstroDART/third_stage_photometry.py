#%%


import os as os
import glob as glob
import numpy as np
import astropy as astro
import astropy.units as u
import h5py
from astropy.coordinates import SkyCoord
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
from astropy.wcs import WCS
from photutils.aperture import CircularAnnulus, CircularAperture, SkyCircularAperture, aperture_photometry, ApertureStats, SkyCircularAnnulus
from astropy.stats import SigmaClip
from astropy.coordinates import EarthLocation
from astropy.time import Time
from .utils import *
from .second_stage import get_fwhm
from matplotlib import gridspec
import matplotlib.pyplot as plt
from astropy.visualization import ZScaleInterval
from tqdm import tqdm
z = ZScaleInterval()



#%%



class get_site_coordinates:
    def __init__(self, coordinates: list[str] = None, observatory_location: str = None):
        self.coordinates = coordinates
        self.observatory_location = observatory_location
    
    def from_lat_lon(self):
        if self.coordinates is not None and self.observatory_location is None:

            location = EarthLocation.from_geodetic(lon=self.coordinates[0], lat=self.coordinates[1], height=self.coordinates[2])

        
        return location

    def from_name(self):

        if self.coordinates is None and self.observatory_location is not None:

            location = EarthLocation.of_site(self.observatory_location)
            
        return location




class check_image:

    def __init__(self,reference_image, threshold, plot: bool = True):

        self.reference_image = reference_image
        self.threshold = threshold
        self.plot = plot

    def run(self):

        data = save_and_load_data(load_name = self.reference_image).load_ccddata_from_fits()

        mean , median, std = sigma_clipped_stats(data.data,sigma=3.0)
        wcs_header = WCS(data.header)

        scale = data.header['SCALE']

        print('Calculating  FWHM')
        fwhms = get_fwhm(files = [self.reference_image]).estimate_fwhm()[0]

        daofind = DAOStarFinder(fwhm=fwhms*scale, threshold=self.threshold*std)  
        sources = daofind(data.data - median)  

        sources.sort('flux')
        sources.reverse()
        print()
        print(sources)

  
        positions = np.transpose((sources['xcentroid'], sources['ycentroid']))
        apertures = CircularAperture(positions, r=20.0)

        if self.plot == True:
            z1,z2 = z.get_limits(data.data)


            gs = gridspec.GridSpec(1, 1) 


            fig = plt.figure(figsize=(7,7))
            ax1 = fig.add_subplot(gs[0],projection=wcs_header)

            ax1.imshow(data.data, cmap='magma', origin='lower', interpolation='nearest',vmin=z1, vmax=z2)
            
            apertures.plot(color='white', lw=1.5, alpha=0.5)

            for ii in range(len(positions)):
                ax1.text(positions[ii][0]+20, positions[ii][1], f'{ii+1}', color='white')

            ax1.coords[0].set_axislabel('Declination',fontsize=12)
            ax1.coords[1].set_axislabel('Right Ascension',fontsize=12)
            ax1.coords[0].set_ticks(color='k', direction='out')
            ax1.coords[1].set_ticks(color='k', direction='out')
            ax1.coords[0].set_ticklabel_visible(True)
            ax1.coords[1].set_ticklabel_visible(True)
    

            ax1.coords[0].set_ticklabel_position('bltr')
            ax1.coords[1].set_ticklabel_position('bltr')
            ax1.coords[0].grid(color='white',linestyle='--',linewidth=0.5)
            ax1.coords[1].grid(color='white',linestyle='--',linewidth=0.5)
            plt.show()

        
        return positions
    

class coordinates:

    def __init__(self, files: list[str] = None, pixel_coordinates: list[float]= None, world_coordinates: list[float]= None, check_reference_image: bool = True, reference_frame: int = None, target_index: int = None, comparison_stars_indeces: list[int] = None):

        self.files = files
        self.check_reference_image = check_reference_image
        self.reference_frame = reference_frame
        self.target_index = target_index
        self.comparison_stars_indeces = comparison_stars_indeces
        self.pixel_coordinates = pixel_coordinates
        self.world_coordinates = world_coordinates
    
    def from_image(self) -> list[str]:

        if self.check_reference_image == True:

            reference_positions = check_image(reference_image = self.files[self.reference_frame], threshold = 5).run()
 
            target_selection = int(input('Please select the target star from the ds9 image display: (e.g. 1) ' )) - 1
            comparison_star_selection = str(input('Please select some comparison stars from the ds9 image display: (e.g. 1,2,3) ' ))
            comparison_star_selection = comparison_star_selection.split(',')
            comparison_star_selection = [int(x)-1 for x in comparison_star_selection]
            
            data = save_and_load_data(load_name = self.files[self.reference_frame]).load_ccddata_from_fits()
            wcs = WCS(data.header)

            target_coordinates = wcs.all_pix2world(reference_positions[target_selection][0],reference_positions[target_selection][1], 1)
            target_coordinates = SkyCoord(target_coordinates[0],target_coordinates[1], frame='icrs', unit='deg')

            all_comparison_star_coordinates = []
            for jj in range(len(comparison_star_selection)):
                print(reference_positions[comparison_star_selection[jj]][0],reference_positions[comparison_star_selection[jj]][1])
                globals()[f'comparison_star_coordinates_{jj}'] = wcs.all_pix2world(reference_positions[comparison_star_selection[jj]][0],reference_positions[comparison_star_selection[jj]][1],1)
                globals()[f'comparison_star_coordinates_{jj}'] = SkyCoord(globals()[f'comparison_star_coordinates_{jj}'][0],globals()[f'comparison_star_coordinates_{jj}'][1], frame='icrs', unit='deg')
                all_comparison_star_coordinates.append(globals()[f'comparison_star_coordinates_{jj}'])
        else:
            raise Exception('Show image selection not provided for checking')
        
        return target_coordinates, all_comparison_star_coordinates
    
    def from_index(self) -> list[str]:

        reference_positions = check_image(reference_image = self.files[self.reference_frame], threshold = 5, plot=False).run()
        
        data = save_and_load_data(load_name = self.files[self.reference_frame]).load_ccddata_from_fits()
        wcs = WCS(data.header)

        target_coordinates = wcs.all_pix2world(reference_positions[self.target_index][0],reference_positions[self.target_index][1], 1)
        target_coordinates = SkyCoord(target_coordinates[0],target_coordinates[1], frame='icrs', unit='deg')

        all_comparison_star_coordinates = []
        for jj in range(len(self.comparison_stars_indeces)):
            globals()[f'comparison_star_coordinates_{jj}'] = wcs.all_pix2world(reference_positions[self.comparison_stars_indeces[jj]][0],reference_positions[self.comparison_stars_indeces[jj]][1],1)
            globals()[f'comparison_star_coordinates_{jj}'] = SkyCoord(globals()[f'comparison_star_coordinates_{jj}'][0],globals()[f'comparison_star_coordinates_{jj}'][1], frame='icrs', unit='deg')
            all_comparison_star_coordinates.append(globals()[f'comparison_star_coordinates_{jj}'])

    
        return target_coordinates, all_comparison_star_coordinates
    
    def px_to_world(self):
        
        full_world_coordinates_list = []
        for jj in range(len(self.files)):
            data = save_and_load_data(load_name = self.files[jj]).load_ccddata_from_fits()
            wcs = WCS(data.header)
            world_coordinates = astro.wcs.utils.pixel_to_skycoord(xp = self.pixel_coordinates[jj][0],yp = self.pixel_coordinates[jj][1], wcs = wcs)    
            full_world_coordinates_list.append(world_coordinates)

            # Returns a list, if correct every point should have the same coordinates, this is intentional and a quick way to debug


        return full_world_coordinates_list
    
    def world_to_px(self):
 
        full_px_coordinates_list = []
        for jj in range(len(self.files)):
            data = save_and_load_data(load_name = self.files[jj]).load_ccddata_from_fits()
            wcs = WCS(data.header)

            px_coordinates = astro.wcs.utils.skycoord_to_pixel(self.world_coordinates, wcs)    
            
            full_px_coordinates_list.append((px_coordinates[0].item(),px_coordinates[1].item()))


        return full_px_coordinates_list
        


        


class photometry:

    def __init__(self, phot_method: str,
        aperture_type: str, 
        files = list[str],
        single_coord: SkyCoord = None,
        target_coord: SkyCoord = None,
        comparison_coord: list = None,
        filters: list[str] = None,
        obs_location: astropy.coordinates.earth.EarthLocation = None, 
        radius_phot: float = None, 
        radius_annulus: float = None, 
        radius_dannulus: float =  None, 
        reference_file: str = None, 
        zmag: float = 25,
        sigma: float = 3,
        save_results: bool = True,
        save_data_dir: str = None,
        date: str = None,
        target_name: str = None,
        overwrite: str = None) -> None:
        
        valid_phot_methods = ['sky', 'pixel']
        if phot_method not in valid_phot_methods:
            raise ValueError(f"Invalid value for phot_method: {phot_method}. Valid options are {valid_phot_methods}")
        
        valid_aperture_types = ['fwhm', 'custom']
        if aperture_type not in valid_aperture_types:
            raise ValueError(f"Invalid value for aperture_type: {aperture_type}. Valid options are {valid_aperture_types}")
        
        self.phot_method = phot_method
        self.aperture_type = aperture_type
        self.files = files
        self.single_coord =  single_coord
        self.target_coord = target_coord
        self.comparison_coord = comparison_coord 
        self.filters = filters
        self.obs_location = obs_location
        self.radius_phot = radius_phot
        self.radius_annulus = radius_annulus
        self.radius_dannulus = radius_dannulus
        self.reference_file = reference_file
        self.zmag = zmag
        self.sigma = sigma
        self.save_results = save_results
        self.save_data_dir = save_data_dir
        self.file_to_phot = None
        self.date = date
        self.target_name = target_name
        self.overwrite = overwrite
        
        
        
        
        
        

    

    def pixel_aperture_photometry(self,file,position):
        
        data = save_and_load_data(load_name = file).load_ccddata_from_fits()

        error  = data.uncertainty.array

        if type(self.obs_location) == str:  
            location = get_site_coordinates(observatory_location=self.obs_location).from_name()

        if type(self.obs_location) == list:  
            location = get_site_coordinates(coordinates=self.obs_location).from_lat_lon()

        gregorian_date = data.header['DATE-OBS']
        t = Time(gregorian_date, format='isot', scale='utc')


        t_tdb = t.tdb

        sky_coord = coordinates(files = [file],pixel_coordinates = [position]).px_to_world()[0]

        barycorr = t_tdb.light_travel_time(sky_coord, location=location)

        timestamp = (t_tdb + barycorr).mjd

        if self.aperture_type == 'fwhm':
            
            radius = 2.5*get_fwhm(files = [file]).estimate_fwhm()[0]
            annulus = 3.5*get_fwhm(files = [file]).estimate_fwhm()[0]
            dannulus = 1.5*get_fwhm(files = [file]).estimate_fwhm()[0] + annulus
            aperture = CircularAperture(position, r=radius)
            annulus_aperture = CircularAnnulus(position, r_in=annulus, r_out=dannulus)

        if self.aperture_type == 'custom':

            aperture = CircularAperture(position, r=self.radius_phot)
            annulus_aperture = CircularAnnulus(position, r_in=self.radius_annulus, r_out=self.radius_dannulus)


        data = data.data

        sigclip = SigmaClip(sigma=self.sigma, maxiters=10)
        
        bkg_stats = ApertureStats(data, annulus_aperture,sigma_clip=sigclip)
        
        bkg_median = bkg_stats.median
        
        phot_table = aperture_photometry(data, aperture,error = error )
        
        aperture_area = aperture.area_overlap(data)
        
        total_bkg = bkg_median * aperture_area
        
        sub_phot = phot_table['aperture_sum'] - total_bkg
        
        print()
        print('----------------------------------------------------------------')
        print('The background level is: %f' %np.median(total_bkg))
        print('The sky corrected phot level is: %f' %np.median(sub_phot))
        print('The background total error level is: %f' %np.median(phot_table['aperture_sum_err']))
        print('----------------------------------------------------------------')
        print()

        counts_err = np.median(phot_table['aperture_sum_err'])
        counts = np.median(phot_table['aperture_sum'] - total_bkg)
        

        
        return  timestamp, counts, counts_err, aperture_area




    def sky_aperture_photometry(self,file,position):
        
        data = save_and_load_data(load_name = file).load_ccddata_from_fits()

        error  = data.uncertainty.array

        wcs_transformation = WCS(data.header)

        if type(self.obs_location) == str:  
            location = get_site_coordinates(observatory_location=self.obs_location).from_name()

        if type(self.obs_location) == list:  
            location = get_site_coordinates(coordinates=self.obs_location).from_lat_lon()


        gregorian_date = data.header['DATE-OBS']
        t = Time(gregorian_date, format='isot', scale='utc')


        t_tdb = t.tdb


        barycorr = t_tdb.light_travel_time(position, location=location)

        timestamp = (t_tdb + barycorr).mjd
       

        if self.aperture_type == 'fwhm':
            
            radius = 2.5*get_fwhm(files = [file]).estimate_fwhm()[0]*float(data.header['SCALE'])
            annulus = 3.5*get_fwhm(files = [file]).estimate_fwhm()[0]*float(data.header['SCALE'])
            dannulus = 1.5*get_fwhm(files = [file]).estimate_fwhm()[0]*float(data.header['SCALE']) + annulus

            aperture = SkyCircularAperture(position, r=radius*u.arcsec)
            annulus_aperture = SkyCircularAnnulus(position, r_in=annulus*u.arcsec, r_out=dannulus*u.arcsec)

        if self.aperture_type == 'custom':

            aperture = SkyCircularAperture(position, r=self.radius_phot*u.arcsec)

            annulus_aperture = SkyCircularAnnulus(position, r_in=self.radius_annulus*u.arcsec, r_out=self.radius_dannulus*u.arcsec)


        data = data.data



        sigclip = SigmaClip(sigma=self.sigma, maxiters=10)
        
        bkg_stats = ApertureStats(data, annulus_aperture,sigma_clip=sigclip,wcs=wcs_transformation)
        
        bkg_median = bkg_stats.median
        
        phot_table = aperture_photometry(data, aperture,error=error,wcs=wcs_transformation)
        

        
        aperture_px = aperture.to_pixel(wcs_transformation)
        
        aperture_area = aperture_px.area
        
        
        aperstats = ApertureStats(data, aperture,wcs=wcs_transformation)
        
        
        total_bkg = bkg_median * aperture_area
        
        sub_phot = phot_table['aperture_sum'] - total_bkg
        
        print()
        print('----------------------------------------------------------------')
        print('The background level is: %f' %np.median(total_bkg))
        print('The sky corrected phot level is: %f' %np.median(sub_phot))
        print('The background total error level is: %f' %np.median(phot_table['aperture_sum_err']))
        print('----------------------------------------------------------------')
        print()
        counts_err = np.median(phot_table['aperture_sum_err'])
        counts = np.median(phot_table['aperture_sum'] - total_bkg)

        return timestamp, counts, counts_err, aperture_area





    def instrumental_flux_to_flux(self,file, counts, counts_err):
        
        data = save_and_load_data(load_name = file).load_ccddata_from_fits()

        exptime = float(data.header['EXPTIME'])
   
        mag_ins =  self.zmag - 2.5*np.log10(counts) + 2.5*np.log10(exptime)
        error = 2.5*(1/(np.log(10)*counts))*counts_err 

        return mag_ins, error




    def save_dict_to_hdf5(self,h5file, path, dictionary):
    
        for key, item in dictionary.items():
            full_path = f"{path}/{key}"
            
            if isinstance(item, dict):
                group = h5file.create_group(full_path)
                self.save_dict_to_hdf5(h5file, full_path, item)
            else:
                h5file.create_dataset(full_path, data=item)

    def run_single_coord(self):
        data_to_save = {
        'object': 
        {
        'filter':
        {
        }
        }
        }

        data_to_save['object']['coords'] = {}


        for yy in range(len(self.filters)):

            locals()[f'timestamps_{self.filters[yy]}'] = []
            locals()[f'counts{self.filters[yy]}'] = []
            locals()[f'counts_err{self.filters[yy]}'] = []
            locals()[f'mag_ins{self.filters[yy]}'] = []
            locals()[f'mag_err{self.filters[yy]}'] = []
            
        

            for ll,file in enumerate(tqdm(self.files[yy])):
                
                if self.phot_method == 'pixel':


                    timestamp, counts, counts_err, aperture_area = self.pixel_aperture_photometry(file,self.single_coord[yy][ll])
                    mag_ins, mag_err = self.instrumental_flux_to_flux(file, counts, counts_err)

                    locals()[f'timestamps_{self.filters[yy]}'].append(timestamp)
                    locals()[f'counts{self.filters[yy]}'].append(counts)
                    locals()[f'counts_err{self.filters[yy]}'].append(counts_err)
                    locals()[f'mag_ins{self.filters[yy]}'].append(mag_ins)
                    locals()[f'mag_err{self.filters[yy]}'].append(mag_err)

                if self.phot_method == 'pixel' and yy == 0:
                    coords_to_save = coordinates(files=[file],pixel_coordinates=[self.single_coord[yy][ll]]).px_to_world()[0]

                    data_to_save['object']['coords']['ra'] = {}
                    data_to_save['object']['coords']['ra']['value'] = coords_to_save.ra.value
                    data_to_save['object']['coords']['ra']['unit'] = 'degree'
                    data_to_save['object']['coords']['dec'] = {}
                    data_to_save['object']['coords']['dec']['value'] = coords_to_save.dec.value
                    data_to_save['object']['coords']['dec']['unit'] = 'degree'


                if self.phot_method == 'sky':


                    timestamp, counts, counts_err, aperture_area = self.sky_aperture_photometry(file,self.single_coord)
                    mag_ins, mag_err = self.instrumental_flux_to_flux(file, counts, counts_err)

                    locals()[f'timestamps_{self.filters[yy]}'].append(timestamp)
                    locals()[f'counts{self.filters[yy]}'].append(counts)
                    locals()[f'counts_err{self.filters[yy]}'].append(counts_err)
                    locals()[f'mag_ins{self.filters[yy]}'].append(mag_ins)
                    locals()[f'mag_err{self.filters[yy]}'].append(mag_err)
                    
                if self.phot_method == 'sky' and yy == 0:


                    data_to_save['object']['coords']['ra'] = {}
                    data_to_save['object']['coords']['ra']['value'] = self.single_coord.ra.value
                    data_to_save['object']['coords']['ra']['unit'] = 'degree'
                    data_to_save['object']['coords']['dec'] = {}
                    data_to_save['object']['coords']['dec']['value'] = self.single_coord.dec.value
                    data_to_save['object']['coords']['dec']['unit'] = 'degree'

    
            data_to_save['object']['filter'][self.filters[yy]] = {}
            
            
            data_to_save['object']['filter'][self.filters[yy]][f'timestamps'] = locals()[f'timestamps_{self.filters[yy]}']
            data_to_save['object']['filter'][self.filters[yy]][f'flux'] = locals()[f'counts{self.filters[yy]}']
            data_to_save['object']['filter'][self.filters[yy]][f'flux_err'] = locals()[f'counts_err{self.filters[yy]}']
            data_to_save['object']['filter'][self.filters[yy]][f'mag_ins'] = locals()[f'mag_ins{self.filters[yy]}']
            data_to_save['object']['filter'][self.filters[yy]][f'mag_err'] = locals()[f'mag_err{self.filters[yy]}']



        if self.save_results == True:


            with h5py.File(self.save_data_dir + 'photometry_results_single_object.h5', 'w') as h5file:
                self.save_dict_to_hdf5(h5file, '/', data_to_save)
    
        return data_to_save




    def run_multi_coord(self):

        data_to_save = {
        'target': 
        {
        'filter':
        {
        }
        },
        'comparison_stars': 
        {
        }
        }

        data_to_save['target']['coords'] = {}




        for yy in range(len(self.filters)):

            locals()[f'target_timestamps_{self.filters[yy]}'] = []
            locals()[f'target_counts{self.filters[yy]}'] = []
            locals()[f'target_counts_err{self.filters[yy]}'] = []
            locals()[f'target_mag_ins{self.filters[yy]}'] = []
            locals()[f'target_mag_err{self.filters[yy]}'] = []
            
        

            for ll,file in enumerate(tqdm(self.files[yy])):
                
                if self.phot_method == 'pixel':


                    timestamp, counts, counts_err, aperture_area = self.pixel_aperture_photometry(file,self.target_coord[yy][ll])
                    mag_ins, mag_err = self.instrumental_flux_to_flux(file, counts, counts_err)

                    locals()[f'target_timestamps_{self.filters[yy]}'].append(timestamp)
                    locals()[f'target_counts{self.filters[yy]}'].append(counts)
                    locals()[f'target_counts_err{self.filters[yy]}'].append(counts_err)
                    locals()[f'target_mag_ins{self.filters[yy]}'].append(mag_ins)
                    locals()[f'target_mag_err{self.filters[yy]}'].append(mag_err)

                if self.phot_method == 'pixel' and yy == 0:
                    coords_to_save = coordinates(files=[file],pixel_coordinates=[self.target_coord[yy][ll]]).px_to_world()[0]

                    data_to_save['target']['coords']['ra'] = {}
                    data_to_save['target']['coords']['ra']['value'] = coords_to_save.ra.value
                    data_to_save['target']['coords']['ra']['unit'] = 'degree'
                    data_to_save['target']['coords']['dec'] = {}
                    data_to_save['target']['coords']['dec']['value'] = coords_to_save.dec.value
                    data_to_save['target']['coords']['dec']['unit'] = 'degree'


                if self.phot_method == 'sky':


                    timestamp, counts, counts_err, aperture_area = self.sky_aperture_photometry(file,self.target_coord)
                    mag_ins, mag_err = self.instrumental_flux_to_flux(file, counts, counts_err)

                    locals()[f'target_timestamps_{self.filters[yy]}'].append(timestamp)
                    locals()[f'target_counts{self.filters[yy]}'].append(counts)
                    locals()[f'target_counts_err{self.filters[yy]}'].append(counts_err)
                    locals()[f'target_mag_ins{self.filters[yy]}'].append(mag_ins)
                    locals()[f'target_mag_err{self.filters[yy]}'].append(mag_err)
                    
                if self.phot_method == 'sky' and yy == 0:


                    data_to_save['target']['coords']['ra'] = {}
                    data_to_save['target']['coords']['ra']['value'] = self.target_coord.ra.value
                    data_to_save['target']['coords']['ra']['unit'] = 'degree'
                    data_to_save['target']['coords']['dec'] = {}
                    data_to_save['target']['coords']['dec']['value'] = self.target_coord.dec.value
                    data_to_save['target']['coords']['dec']['unit'] = 'degree'

    
            data_to_save['target']['filter'][self.filters[yy]] = {}
            
            
            data_to_save['target']['filter'][self.filters[yy]][f'timestamps'] = locals()[f'target_timestamps_{self.filters[yy]}']
            data_to_save['target']['filter'][self.filters[yy]][f'flux'] = locals()[f'target_counts{self.filters[yy]}']
            data_to_save['target']['filter'][self.filters[yy]][f'flux_err'] = locals()[f'target_counts_err{self.filters[yy]}']
            data_to_save['target']['filter'][self.filters[yy]][f'mag_ins'] = locals()[f'target_mag_ins{self.filters[yy]}']
            data_to_save['target']['filter'][self.filters[yy]][f'mag_err'] = locals()[f'target_mag_err{self.filters[yy]}']




        for ww in range(len(self.comparison_coord)):

            data_to_save['comparison_stars'][f'comparison_{str(ww+1)}'] = {}
            data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords'] = {}
            data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['filter'] = {}

            for yy in range(len(self.filters)):

                locals()[f'comparison_{str(ww+1)}_timestamps_{self.filters[yy]}'] = []
                locals()[f'comparison_{str(ww+1)}_counts{self.filters[yy]}'] = []
                locals()[f'comparison_{str(ww+1)}_counts_err{self.filters[yy]}'] = []
                locals()[f'comparison_{str(ww+1)}_mag_ins{self.filters[yy]}'] = []
                locals()[f'comparison_{str(ww+1)}_mag_err{self.filters[yy]}'] = []
                
            

                for ll,file in enumerate(tqdm(self.files[yy])):
                    
                    if self.phot_method == 'pixel':


                        timestamp, counts, counts_err, aperture_area = self.pixel_aperture_photometry(file,self.comparison_coord[ww][yy][ll])
                        mag_ins, mag_err = self.instrumental_flux_to_flux(file, counts, counts_err)

                        locals()[f'comparison_{str(ww+1)}_timestamps_{self.filters[yy]}'].append(timestamp)
                        locals()[f'comparison_{str(ww+1)}_counts{self.filters[yy]}'].append(counts)
                        locals()[f'comparison_{str(ww+1)}_counts_err{self.filters[yy]}'].append(counts_err)
                        locals()[f'comparison_{str(ww+1)}_mag_ins{self.filters[yy]}'].append(mag_ins)
                        locals()[f'comparison_{str(ww+1)}_mag_err{self.filters[yy]}'].append(mag_err)

                    if self.phot_method == 'pixel' and yy == 0:
                        coords_to_save = coordinates(files=[file],pixel_coordinates=[self.comparison_coord[ww][yy][ll]]).px_to_world()[0]

                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['ra'] = {}
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['ra']['value'] = coords_to_save.ra.value
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['ra']['unit'] = 'degree'
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['dec'] = {}
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['dec']['value'] = coords_to_save.dec.value
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['dec']['unit'] = 'degree'


                    if self.phot_method == 'sky':


                        timestamp, counts, counts_err, aperture_area = self.sky_aperture_photometry(file,self.comparison_coord[ww])
                        mag_ins, mag_err = self.instrumental_flux_to_flux(file, counts, counts_err)

                        locals()[f'comparison_{str(ww+1)}_timestamps_{self.filters[yy]}'].append(timestamp)
                        locals()[f'comparison_{str(ww+1)}_counts{self.filters[yy]}'].append(counts)
                        locals()[f'comparison_{str(ww+1)}_counts_err{self.filters[yy]}'].append(counts_err)
                        locals()[f'comparison_{str(ww+1)}_mag_ins{self.filters[yy]}'].append(mag_ins)
                        locals()[f'comparison_{str(ww+1)}_mag_err{self.filters[yy]}'].append(mag_err)
                        
                    if self.phot_method == 'sky' and yy == 0:


                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['ra'] = {}
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['ra']['value'] = self.comparison_coord[ww].ra.value
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['ra']['unit'] = 'degree'
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['dec'] = {}
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['dec']['value'] = self.comparison_coord[ww].dec.value
                        data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['coords']['dec']['unit'] = 'degree'

        
                data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['filter'][self.filters[yy]] = {}
                
                
                data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['filter'][self.filters[yy]][f'timestamps'] = locals()[f'comparison_{str(ww+1)}_timestamps_{self.filters[yy]}']
                data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['filter'][self.filters[yy]][f'flux'] = locals()[f'comparison_{str(ww+1)}_counts{self.filters[yy]}']
                data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['filter'][self.filters[yy]][f'flux_err'] = locals()[f'comparison_{str(ww+1)}_counts_err{self.filters[yy]}']
                data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['filter'][self.filters[yy]][f'mag_ins'] = locals()[f'comparison_{str(ww+1)}_mag_ins{self.filters[yy]}']
                data_to_save['comparison_stars'][f'comparison_{str(ww+1)}']['filter'][self.filters[yy]][f'mag_err'] = locals()[f'comparison_{str(ww+1)}_mag_err{self.filters[yy]}']





        if self.save_results == True:

            if os.path.exists(self.save_data_dir + '/' + self.date + '/' + self.target_name) == False:
                os.mkdir(self.save_data_dir + '/' + self.date + '/' + self.target_name)
                print(f'The photometry directory for date {self.date} and object {self.target_name} has been created')
            elif os.path.exists(self.save_data_dir + '/' + self.date + '/' + self.target_name) == True and self.overwrite=='yes':
                print(f'The photometry directory for date {self.date} and object {self.target_name} already exists and overwrite is set to {self.overwrite}')
                print(f'Overwritting data directory for object {self.target_name} ')
                shutil.rmtree(self.save_data_dir + '/' + self.date + '/' + self.target_name)
                os.makedirs(self.save_data_dir + '/' + self.date + '/' + self.target_name)  
            else:
                print(f'The directory for date {self.date} and object {self.target_name} already exists and overwrite is set to {self.overwrite}')
                print(f'Skipping creation of directory for object {self.target_name} ')
                print()

            with h5py.File(self.save_data_dir + 'photometry_results_target_and_comparison.h5', 'w') as h5file:
                self.save_dict_to_hdf5(h5file, '/', data_to_save)

        return data_to_save 








