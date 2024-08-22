#%%

import subprocess as subprocess
import glob as glob
import os as os
import numpy as np
from astropy.io import fits
import shutil
from pathlib import Path
from ccdproc import ImageFileCollection, combine
from astropy.nddata import CCDData, StdDevUncertainty
from astropy import units as u
import astropy
import numpy
from tempfile import mkdtemp





class data_organiser:

    def __init__(self, uncal_dir ,reduction_dir, date, target, overwrite):
        """Step initializer.
        """

        #self.wdir = wdir # THIS MUST FULLFILL THE STRUCTURE uncal_data, reduced_data and code
        self.date = date
        self.target = target
        self.overwrite = overwrite
        self.uncal_dir = uncal_dir
        self.reduction_dir = reduction_dir


    def get_directory(self):

        reduction_dir_object_name = self.reduction_dir + self.date + '/' + self.target

        return str(reduction_dir_object_name) + '/'
    
    def run(self):


        assertion_uncal_data_dir = os.path.exists(self.uncal_dir) 
        assertion_data_directory = os.path.exists(self.uncal_dir + self.date)
        
        if not assertion_uncal_data_dir or not assertion_data_directory: # this is the pythonic way to check a negation
            raise Exception(f'''The uncalibrated data directory {self.uncal_dir} or the date {self.date} does not 
                exist or has not been found''')
            
        elif len(os.listdir(self.uncal_dir + '/' + self.date)) != 0:
            print(f'Uncal data directory {self.date} found and has data inside')
        else:
            raise Exception(f'Uncal data directory {self.date} found but is empty')



        reduction_dir = self.reduction_dir + self.date 

        overwrite = self.overwrite

        if os.path.exists(reduction_dir) == False:
            os.mkdir(reduction_dir)
            print(f'The reduced data directory for date {self.date} has been created')
        else:
            print(f'The reduced data directory for date {self.date} already exists')
            print('Skipping creation of reduced data directory')
            print()

        object_name = self.target
        reduction_dir_object_name = reduction_dir + '/' +  object_name
        


        if os.path.exists(reduction_dir_object_name) == False:
            os.mkdir(reduction_dir_object_name)
            print(f'The data directory for date {self.date} and object {object_name} has been created')
        elif os.path.exists(reduction_dir_object_name) == True and overwrite=='yes':
            print(f'The data directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
            print(f'Overwritting data directory for object {object_name} ')
            shutil.rmtree(reduction_dir_object_name)
            os.makedirs(reduction_dir_object_name)  
        else:
            print(f'The directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
            print(f'Skipping creation of directory for object {object_name} ')
            print()



        where_uncal_data = str(Path(self.uncal_dir,self.date)) + '/' 


        observation_files_paths = glob.glob(where_uncal_data + '/*.fits')

        bias_files = np.array([],dtype='U120')
        flat_files = np.array([],dtype='U120')
        object_files = np.array([],dtype='U120')
        dark_files = np.array([],dtype='U120')
        flat_dark_files = np.array([],dtype='U120')

        for ii in range(len(observation_files_paths)):
            with fits.open(observation_files_paths[ii]) as hdul:
                header = hdul[0].header
                if 'bias' in header['IMAGETYP'].casefold():
                    bias_files = np.append(bias_files,observation_files_paths[ii])
                if 'flat' in header['IMAGETYP'].casefold():
                    flat_files = np.append(flat_files,observation_files_paths[ii])
                if 'object' in header['IMAGETYP'].casefold() and self.target in header['OBJECT'].casefold():
                    object_files = np.append(object_files,observation_files_paths[ii])
                if 'dark' in header['IMAGETYP'].casefold():
                    dark_files = np.append(dark_files,observation_files_paths[ii])
                if 'flatdark' in header['IMAGETYP'].casefold():
                    flat_dark_files = np.append(flat_dark_files,observation_files_paths[ii])



        filters_flats = np.array(['placeholder'])
        filters_object = np.array(['placeholder'])
        filters_dark_flats = np.array(['placeholder'])


        if len(bias_files) != 0:
            bias_dir_name = reduction_dir_object_name + '/bias/' 


            if os.path.exists(bias_dir_name) == False:
                os.mkdir(bias_dir_name)
                print(f'The bias data directory for date {self.date} and object {object_name} has been created')
            elif os.path.exists(bias_dir_name) == True and overwrite=='yes':
                print(f'The bias data directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Overwritting bias data directory for object {object_name} ')
                shutil.rmtree(bias_dir_name)
                os.makedirs(bias_dir_name)  
            else:
                print(f'The bias directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Skipping creation of bias directory for object {object_name} ')
                print()

            for ii in range(len(bias_files)):
                shutil.copy2(bias_files[ii], bias_files[ii].replace(where_uncal_data,bias_dir_name))

        if len(bias_files) == 0:
            print('No bias files available, skipping')
            print()




        if len(object_files) != 0:
            for jj in range(len(object_files)):
                try:   
                    with fits.open(object_files[jj]) as hdul:
                        header = hdul[0].header
                        band = header['FILTER']
                        if band not in filters_object:
                            filters_object  = np.append(filters_object,band)
                except:
                    pass

            filters_object = np.delete(filters_object,0)
            print('The following filters were found in the object files:')
            if len(filters_object) !=0:
                print(filters_object)

                for ii in range(len(filters_object)):
                    globals()['object_files_' + filters_object[ii]] = np.array([]).astype('<U120')

                for ii in range(len(object_files)):
                    for jj in range(len(filters_object)):
                        with fits.open(object_files[ii]) as hdul:
                            header = hdul[0].header
                            if header['FILTER'] == filters_object[jj]:
                                globals()['object_files_' + filters_object[jj]] = np.append(globals()['object_files_' + filters_object[jj]],object_files[ii])


            else:
                print('None')

            object_dir_name = reduction_dir_object_name + '/object/' 
            if os.path.exists(object_dir_name) == False:
                os.mkdir(object_dir_name)
                print(f'The object data directory for date {self.date} and object {object_name} has been created')
            elif os.path.exists(object_dir_name) == True and overwrite=='yes':
                print(f'The object data directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Overwritting object data directory for object {object_name} ')
                shutil.rmtree(object_dir_name)
                os.makedirs(object_dir_name)  
            else:
                print(f'The object directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Skipping creation of object directory for object {object_name} ')
                print()

            for ii in range(len(filters_object)):
                object_dir_name_with_filter = object_dir_name + filters_object[ii] + '/'
                if os.path.exists(object_dir_name_with_filter) == False:
                    os.mkdir(object_dir_name_with_filter)
                    print(f'The object data directory for date {self.date}, object {object_name} and filter {filters_object[ii]} has been created')
                elif os.path.exists(object_dir_name_with_filter) == True and overwrite=='yes':
                    print(f'The object data directory for date {self.date}, object {object_name} and filter {filters_object[ii]} already exists and overwrite is set to {overwrite}')
                    print(f'Overwritting object data directory for object {object_name} and filter {filters_object[ii]} ')
                    shutil.rmtree(object_dir_name_with_filter)
                    os.makedirs(object_dir_name_with_filter)  
                else:
                    print(f'The object directory for date {self.date}, object {object_name} and filter {filters_object[ii]} already exists and overwrite is set to {overwrite}')
                    print(f'Skipping creation of object directory for object {object_name} and {filters_object[ii]}')
                    print()
                    
                for jj in range(len(globals()['object_files_' + filters_object[ii]])):
                        shutil.copy2(globals()['object_files_' + filters_object[ii]][jj], globals()['object_files_' + filters_object[ii]][jj].replace(where_uncal_data,object_dir_name_with_filter)) 



        if len(object_files) == 0:
            print('No object files available, skipping')
            print()




        if len(flat_files) != 0:
            for jj in range(len(flat_files)): 
                try:  
                    with fits.open(flat_files[jj]) as hdul:
                        header = hdul[0].header
                        band = header['FILTER']
                        if band not in filters_flats:
                            filters_flats  = np.append(filters_flats,band)
                except:
                    pass

            filters_flats = np.delete(filters_flats,0)
            print('The following filters were found in the flat files:')
            if len(filters_flats) !=0:
                print(filters_flats)

                for ii in range(len(filters_flats)):
                    globals()['flat_files_' + filters_flats[ii]] = np.array([]).astype('<U120')

                for ii in range(len(flat_files)):
                    for jj in range(len(filters_flats)):
                        with fits.open(flat_files[ii]) as hdul:
                            header = hdul[0].header
                            if header['FILTER'] == filters_flats[jj]:
                                globals()['flat_files_' + filters_flats[jj]] = np.append(globals()['flat_files_' + filters_flats[jj]],flat_files[ii])

            else:
                print('None')
            flat_dir_name = reduction_dir_object_name + '/flat/' 

            if os.path.exists(flat_dir_name) == False:
                os.mkdir(flat_dir_name)
                print(f'The flat data directory for date {self.date} and object {object_name} has been created')
            elif os.path.exists(flat_dir_name) == True and overwrite=='yes':
                print(f'The flat data directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Overwritting flat data directory for object {object_name} ')
                shutil.rmtree(flat_dir_name)
                os.makedirs(flat_dir_name)  
            else:
                print(f'The flat directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Skipping creation of flat directory for object {object_name} ')
                print()

            for ii in range(len(filters_flats)):
                flat_dir_name_with_filter = flat_dir_name + filters_flats[ii] + '/'
                if os.path.exists(flat_dir_name_with_filter) == False:
                    os.mkdir(flat_dir_name_with_filter)
                    print(f'The flat data directory for date {self.date}, object {object_name} and filter {filters_flats[ii]} has been created')
                elif os.path.exists(flat_dir_name_with_filter) == True and overwrite=='yes':
                    print(f'The flat data directory for date {self.date}, object {object_name} and filter {filters_flats[ii]} already exists and overwrite is set to {overwrite}')
                    print(f'Overwritting flat data directory for object {object_name} and filter {filters_flats[ii]} ')
                    shutil.rmtree(flat_dir_name_with_filter)
                    os.makedirs(flat_dir_name_with_filter)  
                else:
                    print(f'The flat directory for date {self.date}, object {object_name} and filter {filters_flats[ii]} already exists and overwrite is set to {overwrite}')
                    print(f'Skipping creation of flat directory for object {object_name} and {filters_flats[ii]}')
                    print()
                    
                for jj in range(len(globals()['flat_files_' + filters_flats[ii]])):
                        shutil.copy2(globals()['flat_files_' + filters_flats[ii]][jj], globals()['flat_files_' + filters_flats[ii]][jj].replace(where_uncal_data,flat_dir_name_with_filter)) 



        if len(flat_files) == 0:
            print('No flat files available, skipping')
            print()




        if len(flat_dark_files) != 0:

            for jj in range(len(filters_dark_flats)):
                try:   
                    with fits.open(filters_dark_flats[jj]) as hdul:
                        header = hdul[0].header
                        band = header['FILTER']
                        if band not in filters_dark_flats:
                            filters_dark_flats  = np.append(filters_dark_flats,band)
                except:
                    pass
            filters_dark_flats = np.delete(filters_dark_flats,0)
            print('The following filters were found in the flat dark files:')
            if len(filters_dark_flats) !=0:
                print(filters_dark_flats)
                for ii in range(len(filters_dark_flats)):
                    globals()['flat_dark_files' + filters_dark_flats[ii]] = np.array([]).astype('<U120')
                
                for ii in range(len(flat_dark_files)):
                    for jj in range(len(filters_dark_flats)):
                        with fits.open(flat_dark_files[ii]) as hdul:
                            header = hdul[0].header
                            if header['FILTER'] == filters_dark_flats[jj]:
                                globals()['flat_dark_files' + filters_dark_flats[jj]] = np.append(globals()['flat_dark_files' + filters_dark_flats[jj]],flat_dark_files[ii])

            else:
                print('None')
            

            flatdark_dir_name = reduction_dir_object_name + '/flatdark/' 


            if os.path.exists(flatdark_dir_name) == False:
                os.mkdir(flatdark_dir_name)
                print(f'The flatdark data directory for date {self.date} and object {object_name} has been created')
            elif os.path.exists(flatdark_dir_name) == True and overwrite=='yes':
                print(f'The flatdark data directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Overwritting flatdark data directory for object {object_name} ')
                shutil.rmtree(flatdark_dir_name)
                os.makedirs(flatdark_dir_name)  
            else:
                print(f'The flatdark directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Skipping creation of flatdark directory for object {object_name} ')
                print()


            for ii in range(len(filters_dark_flats)):
                flatdark_dir_name_with_filter = flatdark_dir_name + filters_dark_flats[ii] + '/'
                if os.path.exists(flatdark_dir_name_with_filter) == False:
                    os.mkdir(flatdark_dir_name_with_filter)
                    print(f'The flatdark data directory for date {self.date}, object {object_name} and filter {filters_dark_flats[ii]} has been created')
                elif os.path.exists(flatdark_dir_name_with_filter) == True and overwrite=='yes':
                    print(f'The flatdark data directory for date {self.date}, object {object_name} and filter {filters_dark_flats[ii]} already exists and overwrite is set to {overwrite}')
                    print(f'Overwritting flatdark data directory for object {object_name} and filter {filters_dark_flats[ii]} ')
                    shutil.rmtree(flatdark_dir_name_with_filter)
                    os.makedirs(flatdark_dir_name_with_filter)  
                else:
                    print(f'The flatdark directory for date {self.date}, object {object_name} and filter {filters_dark_flats[ii]} already exists and overwrite is set to {overwrite}')
                    print(f'Skipping creation of flatdark directory for object {object_name} and {filters_dark_flats[ii]}')
                    print()
                    
                for jj in range(len(globals()['flatdark_files_' + filters_dark_flats[ii]])):
                        shutil.copy2(globals()['flatdark_files_' + filters_dark_flats[ii]][jj], globals()['flatdark_files_' + filters_dark_flats[ii]][jj].replace(where_uncal_data,flatdark_dir_name_with_filter)) 


        if len(flat_dark_files) == 0:
            print('No flat dark files available, skipping')
            print()




        if len(dark_files) != 0:
            dark_dir_name = reduction_dir_object_name + '/dark/' 


            if os.path.exists(dark_dir_name) == False:
                os.mkdir(dark_dir_name)
                print(f'The dark data directory for date {self.date} and object {object_name} has been created')
            elif os.path.exists(dark_dir_name) == True and overwrite=='yes':
                print(f'The dark data directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Overwritting dark data directory for object {object_name} ')
                shutil.rmtree(dark_dir_name)
                os.makedirs(dark_dir_name)  
            else:
                print(f'The dark directory for date {self.date} and object {object_name} already exists and overwrite is set to {overwrite}')
                print(f'Skipping creation of dark directory for object {object_name} ')
                print()

        if len(dark_files) == 0:
            print('No dark files available, skipping')
            print()
    
    

class save_and_load_data:


    def __init__(self, ccd_data: numpy.ndarray=None, header: astropy.io.fits.header.Header=None, save_name: str=None, load_name: str=None)-> None:
        self.ccd_data = ccd_data
        self.save_name = save_name
        self.load_name = load_name
        self.header = header

    def save_ccddata_to_fits(self) -> None:

        self.header['BUNIT'] =  str(self.ccd_data.unit)
        
        try:

            primary_hdu = fits.PrimaryHDU(data=self.ccd_data.data, header=self.header)

            uncertainty_hdu = fits.ImageHDU(data=self.ccd_data.uncertainty.array, name='UNCERTAINTY')

            hdul = fits.HDUList([primary_hdu, uncertainty_hdu])

            if self.ccd_data.mask is not None:
                mask_hdu = fits.ImageHDU(data=self.ccd_data.mask.astype(int), name='MASK')
                hdul.append(mask_hdu)

            hdul.writeto(self.save_name, overwrite=True)

            
        except:
            print('Uncertainty keyword not found in hdul')
            primary_hdu = fits.PrimaryHDU(data=self.ccd_data.data, header=self.header)

            hdul = fits.HDUList([primary_hdu])

            if self.ccd_data.mask is not None:
                mask_hdu = fits.ImageHDU(data=self.ccd_data.mask.astype(int), name='MASK')
                hdul.append(mask_hdu)
    
    
    
            hdul.writeto(self.save_name, overwrite=True)


    def load_ccddata_from_fits(self):

        with fits.open(self.load_name) as hdul:
            primary_hdu = hdul[0]
            try:
                uncertainty_hdu = hdul['UNCERTAINTY']
                data = primary_hdu.data
                header = primary_hdu.header
                uncertainty = uncertainty_hdu.data
                unit = u.Unit(header['BUNIT'])
                ccd_data = CCDData(data, header=header, unit=unit, uncertainty=StdDevUncertainty(uncertainty))
            except:
                print('Uncertainty keyword not found in hdul')
                data = primary_hdu.data
                header = primary_hdu.header
                unit = u.Unit(header['BUNIT'])
                ccd_data = CCDData(data, header=header, unit=unit)


            if 'MASK' in hdul:
                mask_hdu = hdul['MASK']
                ccd_data.mask = mask_hdu.data.astype(bool)

        return ccd_data




class header_tools:


    def __init__(self, files: str, header_dict: dict=None, header_key: str=None)-> None:
        self.files = files
        self.header_dict = header_dict
        self.header_key = header_key

    def check_full_header(self) -> None:
        for jj in range(len(self.files)):
            with fits.open(self.files[jj]) as hdul:

                header = hdul[0].header
                print(header)

    def check_key_is_present(self) -> None:
        for jj in range(len(self.files)):
            with fits.open(self.files[jj]) as hdul:

                header = hdul[0].header
                if self.header_key is None:
                    raise ValueError ('Header key not provided')
                
                if self.header_key in header:
                    print(True)    
                    print()
                    print(f'The header key {self.header_key} has value {header[self.header_key]}')
                else:
                    print(False)


    def append_header_key(self) -> None:
        for jj in range(len(self.files)):
            with fits.open(self.files[jj],'update') as hdul: 
                
                header = hdul[0].header
                
                if self.header_dict is None:
                    raise ValueError ('Header key dictionary not provided')
                
                else:
                    for ii in range(len(self.header_dict)):
                        header[list(self.header_dict.keys())[ii]] = self.header_dict[list(self.header_dict.keys())[ii]]
                    
                    hdul.flush()



    def change_header_key_name(self) -> None:
        for jj in range(len(self.files)):
            with fits.open(self.files[jj],'update') as hdul: 
                
                header = hdul[0].header
                
                if self.header_dict is None:
                    raise ValueError ('Header key dictionary not provided')
                
                else:
                    for ii in range(len(self.header_dict)):

                        old_key = list(self.header_dict.keys())[ii]
                        new_key = self.header_dict[list(self.header_dict.keys())[ii]]

                        value = header[old_key]
                        comment = header.comments[old_key]
                        
                        header.remove(old_key)
                        header[new_key] = (value, comment)

                    hdul.flush()





    def update_header_values(self) -> None:
        for jj in range(len(self.files)):
            with fits.open(self.files[jj],'update') as hdul:

                header = hdul[0].header
                
                if self.header_dict is None:
                    raise ValueError ('Header key dictionary not provided')
                
                else:
                    for ii in range(len(self.header_dict)):
                        
                        header[list(self.header_dict.keys())[ii]] = (self.header_dict[list(self.header_dict.keys())[ii]])

                    hdul.flush()



class image_combination:
    def __init__(self, wdir: str, files: str, output_name : str, combining_method: str, clipping_method: str = None, minclip: float = None, maxclip: float=None, low_thresh: float = None, high_thresh: float = None, nlow: float = None, nhigh: float = None, minmax_clip_min: float=None, minmax_clip_max: float=None ,weights: numpy.ndarray=None, scale: numpy.ndarray=None, memory_limit: float = 1e9, remove_files: str='yes')-> None:
        self.wdir = wdir
        self.files = files
        self.output_name = output_name
        self.combining_method = combining_method
        self.clipping_method = clipping_method
        self.minclip = minclip
        self.maxclip = maxclip
        self.low_thresh = low_thresh
        self.high_thresh = high_thresh
        self.nlow = nlow
        self.nhigh = nhigh
        self.weights = weights
        self.minmax_clip_min = minmax_clip_min
        self.minmax_clip_max = minmax_clip_max
        self.scale = scale
        self.memory_limit = memory_limit
        self.remove_files = remove_files

    def run(self)-> str:


        tmp_image_folder = Path(mkdtemp(dir=self.wdir, prefix='temp_image_folder_'))
        for ii in range(len(self.files)):
        
            _ = [save_and_load_data(load_name=self.files[ii]).load_ccddata_from_fits().write(str(tmp_image_folder.resolve()) + '/' + self.files[ii].replace(self.wdir,''))]


        ifc = ImageFileCollection(tmp_image_folder)


        if self.clipping_method is not None and self.clipping_method=='minmax':
            self.minmax_clip = True
        else:
            self.minmax_clip = False
        


        if self.clipping_method is not None and self.clipping_method=='sigma_clipping':
            self.sigma_clip = True
        else:
            self.sigma_clip = False



        if self.clipping_method is not None and self.clipping_method=='extrema_clipping':
            self.clip_extrema = True
        else:
            self.clip_extrema = False


        combination = combine(ifc.files_filtered(include_path=True),
                            mem_limit=self.memory_limit,method=self.combining_method,weights=self.weights,scale=self.scale,clip_extrema=self.clip_extrema,nlow=self.nlow,nhigh=self.nhigh,
                            minmax_clip=self.minmax_clip,minmax_clip_min=self.minmax_clip_min,minmax_clip_max=self.minmax_clip_max,
                            sigma_clip=self.sigma_clip,sigma_clip_min=self.low_thresh, sigma_clip_high_thresh=self.high_thresh)
            


        save_and_load_data(ccd_data=combination,save_name=self.wdir + self.output_name,header=combination.header).save_ccddata_to_fits()
        
        if self.remove_files == 'yes':
            shutil.rmtree(tmp_image_folder)



        return  self.wdir + self.output_name

class get_directory:

    def __init__(self, data_dir: str)-> None:
        self.data_dir = data_dir

    def bias(self):
        bias_dir = os.path.join(self.data_dir, 'bias/')
        bias_files = glob.glob(bias_dir + '*.fits')
        return bias_dir, bias_files

    def science(self):

        science_dirs = []
        science_files = []
        
        science_filters = os.listdir(self.data_dir + 'object')
        for ii in range(len(science_filters)):
            science_dirs.append(os.path.join(self.data_dir, 'object', science_filters[ii] + '/'))
            science_files.append(glob.glob(science_dirs[ii] + '/*.fits'))

        return science_dirs, science_files, science_filters
            
    def science_final(self):

        science_dirs = []
        science_files = []
        
        science_filters = os.listdir(self.data_dir)
        for ii in range(len(science_filters)):
            science_dirs.append(os.path.join(self.data_dir, science_filters[ii] + '/'))
            science_files.append(glob.glob(science_dirs[ii] + '/*.fits'))

        return science_dirs, science_files, science_filters
    
    def flatfield(self):
    
        flatfield_dirs = []
        flatfield_files = []
        
        flatfield_filters = os.listdir(self.data_dir + 'flat')
        for ii in range(len(flatfield_filters)):
            flatfield_dirs.append(os.path.join(self.data_dir, 'flat', flatfield_filters[ii] + '/'))
            flatfield_files.append(glob.glob(flatfield_dirs[ii] + '/*.fits'))
            
        return flatfield_dirs, flatfield_files, flatfield_filters

    def dark(self):
    
        dark_dirs = []
        dark_files = []
            
        dark_filters = os.listdir(self.data_dir + 'dark')
        for ii in range(len(dark_filters)):
                dark_dirs.append(os.path.join(self.data_dir, 'dark', dark_filters[ii] + '/'))
                dark_files.append(glob.glob(dark_dirs[ii] + '/*.fits'))
                
        return dark_dirs, dark_files, dark_filters


    def flatdark(self):
    
        flatdark_dirs = []
        flatdark_files = []
            
        flatdark_filters = os.listdir(self.data_dir + 'flatdark')
        for ii in range(len(flatdark_filters)):
                flatdark_dirs.append(os.path.join(self.data_dir, 'flardark', flatdark_filters[ii] + '/'))
                flatdark_files.append(glob.glob(flatdark_dirs[ii] + '/*.fits'))
                
        return flatdark_dirs, flatdark_files, flatdark_filters








