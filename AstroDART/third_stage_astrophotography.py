#%%


import os as os
import glob as glob
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from .utils import *
from matplotlib import gridspec
import matplotlib.pyplot as plt
from astropy.visualization import ZScaleInterval
from tqdm import tqdm
from PIL import Image
from ccdproc import wcs_project
from astropy.visualization import make_lupton_rgb

z = ZScaleInterval()



#%%




class align:

    def __init__(self,files_to_align: list[str], reference_frame: str, directories: list[str]):
        self.files_to_align = files_to_align
        self.reference_frame = reference_frame
        self.directories = directories

    def run(self):

        results = []

        target_data = save_and_load_data(load_name=self.reference_frame).load_ccddata_from_fits()
        
        target_wcs = WCS(target_data.header)
        
        print(type(target_data))
        for ii in tqdm(range(len(self.files_to_align))):
            filter_results = []
            for jj in range(len(self.files_to_align[ii])): 

                

                data_to_align = save_and_load_data(load_name=self.files_to_align[ii][jj]).load_ccddata_from_fits()

                data_to_align_wcs = WCS(data_to_align.header)

                data_to_align.wcs = data_to_align_wcs

                reprojected_image = wcs_project(data_to_align, target_wcs)

                header = reprojected_image.header

                filter_results.append(self.files_to_align[ii][jj].replace(self.directories[ii],self.directories[ii]  + 'aligned_'))

                save_and_load_data(save_name=self.files_to_align[ii][jj].replace(self.directories[ii] ,self.directories[ii]  + 'aligned_') , header = header,ccd_data=reprojected_image).save_ccddata_to_fits()

            results.append(filter_results)

        return results


class save_to_tiff:

    def __init__(self, files: list[str], directories: list[str], filters: list[str], astro_directory: str, date: str, target_name = str, overwrite= str):
        self.files = files
        self.directories = directories
        self.filter = filters
        self.astro_directory = astro_directory
        self.date = date
        self.target_name = target_name
        self.overwrite = overwrite

    def run(self):
        for ii in range(len(self.directories)):
            with fits.open(self.files[ii]) as hdul:
                
                data = hdul[0].data

            data = np.log10(data - np.min(data) + 1)



            data_normalized = (255 * (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data)))



            if os.path.exists(self.astro_directory + '/' + self.date + '/' + self.target_name) == False:
                os.mkdir(self.astro_directory + '/' + self.date + '/' + self.target_name)
                print(f'The photometry directory for date {self.date} and object {self.target_name} has been created')
            elif os.path.exists(self.astro_directory + '/' + self.date + '/' + self.target_name) == True and self.overwrite=='yes':
                print(f'The photometry directory for date {self.date} and object {self.target_name} already exists and overwrite is set to {self.overwrite}')
                print(f'Overwritting data directory for object {self.target_name} ')
                shutil.rmtree(self.astro_directory + '/' + self.date + '/' + self.target_name)
                os.makedirs(self.astro_directory + '/' + self.date + '/' + self.target_name)  
            else:
                print(f'The directory for date {self.date} and object {self.target_name} already exists and overwrite is set to {self.overwrite}')
                print(f'Skipping creation of directory for object {self.target_name} ')
                print()




            img = Image.fromarray(data_normalized)
            img.save(self.astro_directory + '/' + self.date + '/' + self.target_name + '_' + self.filters[ii] + '.tiff')



class rgb_image():

    def __init__(self, red_image, green_image, blue_image, red_stretch: float = 1, green_stretch: float = 1, blue_stretch: float = 1):
        self.red_image = red_image
        self.green_image = green_image
        self.blue_image = blue_image
        self.red_stretch = red_stretch
        self.green_stretch = green_stretch
        self.blue_stretch = blue_stretch
    
    def show(self):
        

        red = save_and_load_data(load_name=self.red_image).load_ccddata_from_fits()
        wcs_header = WCS(red.header)
        red = red.data
        green = save_and_load_data(load_name=self.green_image).load_ccddata_from_fits().data
        blue = save_and_load_data(load_name=self.blue_image).load_ccddata_from_fits().data


        red = np.log1p(red)
        green = np.log1p(green)
        blue = np.log1p(blue)


        stretch_red = self.red_stretch 
        stretch_green = self.green_stretch
        stretch_blue = self.blue_stretch

        red_normalized = (255 * (red - np.nanmin(red)) / (np.nanmax(red) - np.nanmin(red))) * stretch_red
        green_normalized = (255 * (green - np.nanmin(green)) / (np.nanmax(green) - np.nanmin(green))) * stretch_green
        blue_normalized = (255 * (blue - np.nanmin(blue)) / (np.nanmax(blue) - np.nanmin(blue))) * stretch_blue

        red_renormalized = 255 * (red_normalized - np.nanmin(red_normalized)) / (np.nanmax(red_normalized) - np.nanmin(red_normalized))
        green_renormalized = 255 * (green_normalized - np.nanmin(green_normalized)) / (np.nanmax(green_normalized) - np.nanmin(green_normalized))
        blue_renormalized = 255 * (blue_normalized - np.nanmin(blue_normalized)) / (np.nanmax(blue_normalized) - np.nanmin(blue_normalized))


        rgb_default = make_lupton_rgb(red_renormalized, green_renormalized, blue_renormalized, Q=10, stretch=0.5)






        z1,z2 = z.get_limits(rgb_default)


        gs = gridspec.GridSpec(1, 1) 


        fig = plt.figure(figsize=(7,7))
        ax1 = fig.add_subplot(gs[0],projection=wcs_header)

        ax1.imshow(rgb_default, origin='lower', interpolation='nearest')#,vmin=z1, vmax=z2)


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

