# Import necessary modules
#%%
import subprocess as subprocess
import glob as glob
from astropy import units as u
import os as os
import shutil
import ccdproc
from .utils import save_and_load_data





class trimmer:


    def __init__(self, wdir: str, files: list[str], region: str, overwrite: str)-> None:


        self.wdir = wdir
        self.region = region
        self.files = files
        self.overwrite = overwrite
        os.chdir(wdir)

    def run(self) -> list[str]:
        results = []
        if self.overwrite == 'yes':
            files_to_del = glob.glob(self.wdir+ 'trimmed_*')
            for ii in range(len(files_to_del)):
                os.remove(files_to_del[ii])

            for file in self.files:
                print(file.replace(self.wdir,'')) 
                data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                header = data.header
                trimmed = ccdproc.trim_image(data,fits_section=self.region)

                results.append(file.replace(self.wdir,self.wdir + 'trimmed_'))
                save_and_load_data(ccd_data=trimmed,header=header,save_name=file.replace(self.wdir,self.wdir + 'trimmed_')).save_ccddata_to_fits()

        else:
            if len(glob.glob(self.wdir + 'trimmed_*')) ==0: 
                for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header

                    trimmed = ccdproc.trim_image(data,fits_section=self.region)

                    results.append(file.replace(self.wdir,self.wdir + 'trimmed_'))
                    save_and_load_data(ccd_data=trimmed,header=header,save_name=file.replace(self.wdir,self.wdir + 'trimmed_')).save_ccddata_to_fits()

            else:
                results = list(glob.glob(self.wdir + 'trimmed_*'))
                print('Files already exist')
        
        return results


class overscan_correction:


    def __init__(self, wdir: str, files: list[str], region: str, overscan_axis, overwrite: str)-> None:


        self.wdir = wdir 
        self.region = region
        self.files = files
        self.overwrite = overwrite
        self.overscan_axis = overscan_axis
        os.chdir(wdir)

    def run(self) -> list[str]:
        results = []
        if self.overwrite == 'yes':

            files_to_del = glob.glob(self.wdir+ 'overscan_*')
            for ii in range(len(files_to_del)):
                os.remove(files_to_del[ii])

            for file in self.files:
                print(file.replace(self.wdir,'')) 
                data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                header = data.header
                oscan_subtracted = ccdproc.subtract_overscan(data,fits_section=self.region,overscan_axis=self.overscan_axis)

                results.append(file.replace(self.wdir,self.wdir + 'overscan_'))
                save_and_load_data(ccd_data=oscan_subtracted,header=header,save_name=file.replace(self.wdir,self.wdir + 'overscan_')).save_ccddata_to_fits()

        else:
            if len(glob.glob(self.wdir + 'overscan_*')) ==0: 
                for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header
                    oscan_subtracted = ccdproc.subtract_overscan(data,fits_section=self.region,overscan_axis=self.overscan_axis)

                    results.append(file.replace(self.wdir,self.wdir + 'overscan_'))
                    save_and_load_data(ccd_data=oscan_subtracted,header=header,save_name=file.replace(self.wdir,self.wdir + 'overscan_')).save_ccddata_to_fits()

            else:
                results = list(glob.glob(self.wdir + 'overscan_*'))
                print('Files already exist')
        
        return results


class deviation_calculation:

    def __init__(self, wdir: str, files: list[str], overwrite: str, ron=None, gain=None)-> None:
        """
        This function performs the deviation calculation for a list of FITS files.
        It reads the gain and readout noise values from the FITS headers, if not provided.
        If the gain or readout noise values are not found in the headers and not specified in the class call,
        a ValueError is raised.
        The function then applies the deviation calculation using the ccdproc.create_deviation method.
        The processed files are saved with a 'dc_' prefix in the working directory.

        Parameters:
        - self (deviation_calculation): The instance of the deviation_calculation class.

        Returns:
        - results (list[str]): A list of paths to the processed FITS files.
        """

        self.wdir = wdir 
        self.overwrite = overwrite
        self.gain = gain # IF NOT SPECIFIED IN THE HEADER
        self.ron = ron
        self.files = files
        os.chdir(wdir)

    def run(self) -> list[str]:
        results = []

        if self.overwrite == 'yes':

            files_to_del = glob.glob(self.wdir+ 'dc_*')
            for ii in range(len(files_to_del)):
                os.remove(files_to_del[ii])

            for file in self.files:
                print(file.replace(self.wdir,'')) 
                data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                header = data.header


                try:
                    gain = header['gain']
                except:
                    gain = self.gain

                try:
                    ron = header['ron']
                except:
                    ron = self.ron

                if gain==None:
                    raise ValueError('Gain not found in the header and/or not specified in the call to the class')
                if gain==None:
                    raise ValueError('Read Out Noise not found in the header and/or not specified in the call to the class')
                

                data_with_deviation = ccdproc.create_deviation(data, gain=gain * u.electron/u.adu, readnoise=ron * u.electron)


                results.append(file.replace(self.wdir,self.wdir + 'dc_'))
                save_and_load_data(ccd_data=data_with_deviation,header=header,save_name=file.replace(self.wdir,self.wdir + 'dc_')).save_ccddata_to_fits()

        else:
            if len(glob.glob(self.wdir + 'dc_*')) ==0: 
                for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header


                    try:
                        gain = header['gain']
                    except:
                        gain = self.gain

                    try:
                        ron = header['ron']
                    except:
                        ron = self.ron

                    if gain==None:
                        raise ValueError('Gain not found in the header and/or not specified in the call to the class')
                    if gain==None:
                        raise ValueError('Read Out Noise not found in the header and/or not specified in the call to the class')
                    

                    data_with_deviation = ccdproc.create_deviation(data, gain=gain * u.electron/u.adu, readnoise=ron * u.electron)


                    results.append(file.replace(self.wdir,self.wdir + 'dc_'))
                    save_and_load_data(ccd_data=data_with_deviation,header=header,save_name=file.replace(self.wdir,self.wdir + 'dc_')).save_ccddata_to_fits()

            else:
                results = list(glob.glob(self.wdir + 'dc_*'))
                print('Files already exist')
        
        return results





class gain_correction:

    

    def __init__(self, wdir: str, files: list[str], overwrite: str, gain: float = None) -> None:
        """
        Initialize the gain correction step.

        This class is used to correct the gain of the images. It takes a list of files,
        a working directory, an overwrite flag, and an optional gain value. The gain value
        can be specified in the header of the FITS files or provided as an argument to the class.
        If the gain value is not found in the header and not provided as an argument, a ValueError
        will be raised.

        Parameters:
        - wdir (str): The working directory where the input and output files are located.
                    It must follow the structure: uncal_data, reduced_data, and code.
        - files (list[str]): A list of FITS files to be processed.
        - overwrite (str): A flag indicating whether to overwrite existing output files.
                        Accepted values are 'yes' or 'no'.
        - gain (float, optional): The gain value to be used for gain correction.
                                If not provided, it will be read from the FITS header.

        Returns:
        None
        """
        self.wdir = wdir  # The working directory
        self.overwrite = overwrite  # Overwrite flag
        self.gain = gain  # Gain value
        self.files = files  # List of FITS files
        os.chdir(wdir)  # Change the current working directory to the specified working directory

    def run(self) -> list[str]:
        """
        Step initializer for the gain correction process.

        This function iterates through a list of FITS files, applies gain correction, and saves the processed files.
        If the overwrite flag is set to 'yes', existing output files will be overwritten.

        Parameters:
        - self (gain_correct): The instance of the gain_correct class.

        Returns:
        - results (list[str]): A list of paths to the processed FITS files.
        """

        results = []
        if self.overwrite == 'yes':

            files_to_del = glob.glob(self.wdir+ 'gc_*')
            for ii in range(len(files_to_del)):
                os.remove(files_to_del[ii])


            for file in self.files:
                print(file.replace(self.wdir,''))  
                
                data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                header = data.header
                try:
                    gain = header['gain']
                except:
                    gain = self.gain

                if gain==None:
                    raise ValueError('Gain not found in the header and/or not specified in the call to the class')

                gain_corrected = ccdproc.gain_correct(data, gain*u.electron/u.adu)

                results.append(file.replace(self.wdir,self.wdir + 'gc_'))
                save_and_load_data(ccd_data=gain_corrected,header=header,save_name=file.replace(self.wdir,self.wdir + 'gc_')).save_ccddata_to_fits()

        else:
            if len(glob.glob(self.wdir + 'gc_*')) ==0: 
                for file in self.files:
                    print(file.replace(self.wdir,''))  
                   
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header
                    try:
                        gain = header['gain']
                    except:
                        gain = self.gain

                    if gain==None:
                        raise ValueError('Gain not found in the header and/or not specified in the call to the class')

                    gain_corrected = ccdproc.gain_correct(data, gain*u.electron/u.adu)

                    results.append(file.replace(self.wdir,self.wdir + 'gc_'))
                    save_and_load_data(ccd_data=gain_corrected,header=header,save_name=file.replace(self.wdir,self.wdir + 'gc_')).save_ccddata_to_fits()

            else:
                results = list(glob.glob(self.wdir + 'gc_*'))
                print('Files already exist')
        
        return results



class cosmic_ray_laplacian_correction:


    def __init__(self, wdir: str, files: list[str], overwrite: str, gain: float = None, sigclip: float=5) -> None:    

        self.wdir = wdir  # The working directory
        self.overwrite = overwrite  # Overwrite flag
        self.gain = gain  # Gain value
        self.files = files  # List of FITS files
        self.sigclip = sigclip
        os.chdir(wdir)  # Change the current working directory to the specified working directory
    
    
    def run(self) -> list[str]:


        results = []
        if self.overwrite == 'yes':

            files_to_del = glob.glob(self.wdir+ 'crlc_*')
            for ii in range(len(files_to_del)):
                os.remove(files_to_del[ii])


            for file in self.files:
                print(file.replace(self.wdir,'')) 
                data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                header = data.header
                try:
                    gain = header['gain']
                except:
                    gain = self.gain

                if gain==None:
                    raise ValueError('Gain not found in the header and/or not specified in the call to the class')

                cr_cleaned = ccdproc.cosmicray_lacosmic(data, sigclip=self.sigclip)
                results.append(file.replace(self.wdir,self.wdir + 'crlc_'))
                save_and_load_data(ccd_data=cr_cleaned,header=header,save_name=file.replace(self.wdir,self.wdir + 'crlc_')).save_ccddata_to_fits()

        else:
            if len(glob.glob(self.wdir + 'crlc_*')) ==0: 
                for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header
                    try:
                        gain = header['gain']
                    except:
                        gain = self.gain

                    if gain==None:
                        raise ValueError('Gain not found in the header and/or not specified in the call to the class')

                    cr_cleaned = ccdproc.cosmicray_lacosmic(data, sigclip=self.sigclip)
                    results.append(file.replace(self.wdir,self.wdir + 'crlc_'))
                    save_and_load_data(ccd_data=cr_cleaned,header=header,save_name=file.replace(self.wdir,self.wdir + 'crlc_')).save_ccddata_to_fits()

            else:
                results = list(glob.glob(self.wdir + 'crlc_*'))
                print('Files already exist')
        
        return results
    





class cosmic_ray_median_correction:


    def __init__(self, wdir: str, files: list[str], overwrite: str, gain: float = None, mbox: float = 11, rbox: float = 11, gbox: float = 5) -> None:    

        self.wdir = wdir  # The working directory
        self.overwrite = overwrite  # Overwrite flag
        self.gain = gain  # Gain value
        self.files = files  # List of FITS files
        self.mbox = mbox
        self.rbox = rbox
        self.gbox = gbox
        os.chdir(wdir)  # Change the current working directory to the specified working directory
    
    
    def run(self) -> list[str]:


        results = []
        if self.overwrite == 'yes':

            files_to_del = glob.glob(self.wdir+ 'crmed_*')
            for ii in range(len(files_to_del)):
                os.remove(files_to_del[ii])

            for file in self.files:
                print(file.replace(self.wdir,'')) 
                data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                header = data.header
                try:
                    gain = header['gain']
                except:
                    gain = self.gain

                if gain==None:
                    raise ValueError('Gain not found in the header and/or not specified in the call to the class')
                cr_cleaned = ccdproc.cosmicray_median(data, mbox=self.mbox, rbox=self.rbox, gbox=self.gbox)

                results.append(file.replace(self.wdir,self.wdir + 'crmed_'))
                save_and_load_data(ccd_data=cr_cleaned,header=header,save_name=file.replace(self.wdir,self.wdir + 'crmed_')).save_ccddata_to_fits()

                
        else:
            if len(glob.glob(self.wdir + 'crmed_*')) ==0: 
                for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header
                    try:
                        gain = header['gain']
                    except:
                        gain = self.gain

                    if gain==None:
                        raise ValueError('Gain not found in the header and/or not specified in the call to the class')
                    cr_cleaned = ccdproc.cosmicray_median(data, mbox=self.mbox, rbox=self.rbox, gbox=self.gbox)

                    results.append(file.replace(self.wdir,self.wdir + 'crmed_'))
                    save_and_load_data(ccd_data=cr_cleaned,header=header,save_name=file.replace(self.wdir,self.wdir + 'crmed_')).save_ccddata_to_fits()

            else:
                results = list(glob.glob(self.wdir + 'crmed_*'))
                print('Files already exist')
        
        return results

class subtract_bias:

    def __init__(self, wdir: str, files: list[str], masterbias_file: str, overwrite: str) -> None:

        self.wdir = wdir  # The working directory
        self.files = files  # List of FITS files
        self.masterbias_file = masterbias_file  # Master bias file
        self.overwrite = overwrite  # Overwrite flag

    def run(self) -> list[str]:

        results = []
        if self.overwrite == 'yes':
            files_to_del = glob.glob(self.wdir+ 'bias_subtracted_*')
            for ii in range(len(files_to_del)):
                os.remove(files_to_del[ii])

            masterbias_data = save_and_load_data(load_name=self.masterbias_file).load_ccddata_from_fits()
            for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header

                    bias_subtracted = ccdproc.subtract_bias(data, masterbias_data)

                    results.append(file.replace(self.wdir,self.wdir + 'bias_subtracted_'))
                    save_and_load_data(ccd_data=bias_subtracted,header=header,save_name=file.replace(self.wdir,self.wdir + 'bias_subtracted_')).save_ccddata_to_fits()

        else:

            if len(glob.glob(self.wdir + 'bias_subtracted_*')) == 0: 
                files_to_del = glob.glob(self.wdir+ 'bias_subtracted_*')
                for ii in range(len(files_to_del)):
                    os.remove(files_to_del[ii])

                masterbias_data = save_and_load_data(load_name=self.masterbias_file).load_ccddata_from_fits()
                for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header

                    bias_subtracted = ccdproc.subtract_bias(data, masterbias_data)

                    results.append(file.replace(self.wdir,self.wdir + 'bias_subtracted_'))
                    save_and_load_data(ccd_data=bias_subtracted,header=header,save_name=file.replace(self.wdir,self.wdir + 'bias_subtracted_')).save_ccddata_to_fits()


            else:
                results = list(glob.glob(self.wdir + 'bias_subtracted_*'))
                print('Files already exist')
        
        return results







class subtract_dark:

    def __init__(self, wdir: str, files: list[str], masterdark_file: str, overwrite: str) -> None:

        self.wdir = wdir  # The working directory
        self.files = files  # List of FITS files
        self.masterdark_file = masterdark_file  # Master dark file
        self.overwrite = overwrite  # Overwrite flag

    def run(self) -> list[str]:

        results = []
        if self.overwrite == 'yes':
            files_to_del = glob.glob(self.wdir+ 'dark_subtracted_*')
            for ii in range(len(files_to_del)):
                os.remove(files_to_del[ii])

            masterdark_data = save_and_load_data(load_name=self.masterdark_file).load_ccddata_from_fits()
            for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header

                    dark_subtracted = ccdproc.subtract_dark(data, masterdark_data)

                    results.append(file.replace(self.wdir,self.wdir + 'dark_subtracted_'))
                    save_and_load_data(ccd_data=dark_subtracted,header=header,save_name=file.replace(self.wdir,self.wdir + 'dark_subtracted_')).save_ccddata_to_fits()

        else:

            if len(glob.glob(self.wdir + 'dark_subtracted_*')) == 0: 
                files_to_del = glob.glob(self.wdir+ 'dark_subtracted_*')
                for ii in range(len(files_to_del)):
                    os.remove(files_to_del[ii])

                masterdark_data = save_and_load_data(load_name=self.masterdark_file).load_ccddata_from_fits()
                for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header

                    dark_subtracted = ccdproc.subtract_dark(data, masterdark_data)

                    results.append(file.replace(self.wdir,self.wdir + 'dark_subtracted_'))
                    save_and_load_data(ccd_data=dark_subtracted,header=header,save_name=file.replace(self.wdir,self.wdir + 'dark_subtracted_')).save_ccddata_to_fits()


            else:
                results = list(glob.glob(self.wdir + 'dark_subtracted_*'))
                print('Files already exist')
        
        return results




class correct_flatfield:
    def __init__(self, wdir: str, files: list[str], masterflatfield_file: str, overwrite: str) -> None:

        self.wdir = wdir  # The working directory
        self.files = files  # List of FITS files
        self.masterflatfield_file = masterflatfield_file  # Master dark file
        self.overwrite = overwrite  # Overwrite flag

    def run(self) -> list[str]:

        results = []
        if self.overwrite == 'yes':
            files_to_del = glob.glob(self.wdir+ 'flatfield_corrected_*')
            for ii in range(len(files_to_del)):
                os.remove(files_to_del[ii])

            masterflatfield_data = save_and_load_data(load_name=self.masterflatfield_file).load_ccddata_from_fits()
            for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header

                    reduced_data = ccdproc.flat_correct(data, masterflatfield_data)
                    
                    results.append(file.replace(self.wdir,self.wdir + 'flatfield_corrected_'))
                    save_and_load_data(ccd_data=reduced_data,header=header,save_name=file.replace(self.wdir,self.wdir + 'flatfield_corrected_')).save_ccddata_to_fits()

        else:

            if len(glob.glob(self.wdir + 'flatfield_corrected_*')) == 0: 
                files_to_del = glob.glob(self.wdir+ 'flatfield_corrected_*')
                for ii in range(len(files_to_del)):
                    os.remove(files_to_del[ii])

                masterflatfield_data = save_and_load_data(load_name=self.masterflatfield_file).load_ccddata_from_fits()
                for file in self.files:
                    print(file.replace(self.wdir,'')) 
                    data = save_and_load_data(load_name=file).load_ccddata_from_fits()
                    header = data.header

                    reduced_data = ccdproc.flat_correct(data, masterflatfield_data)
                    
                    results.append(file.replace(self.wdir,self.wdir + 'flatfield_corrected_'))
                    save_and_load_data(ccd_data=reduced_data,header=header,save_name=file.replace(self.wdir,self.wdir + 'flatfield_corrected_')).save_ccddata_to_fits()


            else:
                results = list(glob.glob(self.wdir + 'flatfield_corrected_*'))
                print('Files already exist')
        
        return results




class finalize_stage1:

    def __init__(self, data_dir: str, object_dir: str,  bias_dir: str  = None, dark_dir: str= None, flatfield_dir: str= None,flatdark_dir: str= None) -> None:

        self.data_dir = data_dir
        self.bias_dir = bias_dir  # The working directory
        self.flatfield_dir = flatfield_dir # The flat field directory
        self.flatdark_dir = flatdark_dir # The flat dark directory
        self.object_dir = object_dir  # Object directory
        self.dark_dir = dark_dir # The darks directory

    def run(self)->list[str]:

        directories = []
        files = []

        if self.bias_dir is not None:
            shutil.rmtree(self.bias_dir)


        if self.dark_dir is not None:
            for ii in range(len(self.dark_dir)):
                shutil.rmtree(self.dark_dir[ii])


        if self.flatfield_dir is not None:
            for ii in range(len(self.flatfield_dir)):
                shutil.rmtree(self.flatfield_dir[ii])


        if self.flatdark_dir is not None:
            for ii in range(len(self.daflatdark_dirrk_dir)):
                shutil.rmtree(self.flatdark_dir[ii])

        

        for ii in range(len(self.object_dir)):
            all_files = glob.glob(self.object_dir[ii] + '*')

            files_to_keep = glob.glob(self.object_dir[ii] + 'flatfield_corrected_*')

            files_to_del = [file for file in all_files if file not in files_to_keep]

            for file in files_to_del:
                os.remove(file)

            shutil.move(self.object_dir[ii],self.data_dir)
            
        
            
            directories.append(self.object_dir[ii].replace('/object',''))

            files.append(glob.glob(directories[ii] + '*.fits'))

        shutil.rmtree(self.data_dir + 'flat')
        shutil.rmtree(self.data_dir + 'object')

        return directories, files
















