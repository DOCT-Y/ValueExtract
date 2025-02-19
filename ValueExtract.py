# version:20250219 update test_if_match function to detect mismatch between mask and images.
import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew
import SimpleITK as sitk
from tqdm import tqdm

from multiprocessing import cpu_count, Pool
import os
import signal
import time
from typing import Dict, List, Tuple



def compute_statistics_core(arr:np.ndarray, mask:np.ndarray, prefix:str='', 
                       percentiles:List[int]=[5, 25, 50, 75, 95]):
    statistics = {}
    masked_arr = arr[mask>0]

    # compute mean & std
    statistics[f'{prefix}_mean'] = masked_arr.mean()
    statistics[f'{prefix}_std'] = masked_arr.std()

    # compute percentiles
    percentile_values = np.percentile(masked_arr, q=percentiles)
    for percentile_value, percentile in zip(percentile_values, percentiles):
        statistics[f'{prefix}_p{percentile}'] = percentile_value
    
    # compute skewness and kurtosis
    statistics[f'{prefix}_skewness'] = skew(masked_arr)
    statistics[f'{prefix}_kurtosis'] = kurtosis(masked_arr)

    return statistics


def compute_statistics(arr:np.ndarray, mask:np.ndarray, prefix:str='', percentiles:List[int]=[5, 25, 50, 75, 95], slice_statistics:bool=False):
    # compute whole mask statistics
    statistics = compute_statistics_core(arr=arr, mask=mask, prefix=prefix, percentiles=percentiles)

    if not slice_statistics:
        return statistics
    
    # if slice_statistics == True, compute slice mask statistics
    for slice_ind in range(arr.shape[0]):
        if mask[slice_ind, :, :].sum() == 0:
            continue

        statistics.update(compute_statistics_core(
            arr=arr[slice_ind, :, :], 
            mask=mask[slice_ind, :, :], 
            prefix=f'{prefix}-slice-{slice_ind}', 
            percentiles=percentiles
            ))


def test_if_match(root_dir:str, mask_file_name:str, image_file_names:Dict[str, str]):
    image_file_names = list(image_file_names.values())

    checklist = [mask_file_name] + image_file_names

    cases = os.listdir(root_dir)
    cases.sort()

    for case in cases:
        file_dir_list = {k:False for k in checklist}

        for dirpath, dirnames, filenames in os.walk(os.path.join(root_dir, case)):
            for filename in filenames:
                if filename in file_dir_list:
                    file_dir_list[filename] = os.path.join(dirpath, filename)
        
        if all(file_dir_list.values()):
            for file_1_name, file_1_dir in file_dir_list.items():
                for file_2_name, file_2_dir in file_dir_list.items():
                    if file_1_name == file_2_name:
                        continue

                    data_1 = sitk.ReadImage(file_1_dir)
                    data_2 = sitk.ReadImage(file_2_dir)

                    data_1_size = data_1.GetSize()
                    data_2_size = data_2.GetSize()
                    if data_1_size != data_2_size:
                        print(f'size mismatch in {file_1_dir} (size: {data_1_size}) and {file_2_dir} (size: {data_2_size})')


class ValueExtractor:
    def __init__(self, root_dir:str, output_dir:str, mask_file_name:str, image_file_names:Dict[str, str], percentiles:List[int]=[5, 25, 50, 75, 95], slice_statistics:bool=False) -> None:
        self.output_dir = output_dir
        self.percentiles = percentiles
        self.slice_statistics = slice_statistics
        self.mask_filters = None

        image_names = list(image_file_names.keys())
        image_file_names = list(image_file_names.values())

        checklist = [mask_file_name] + image_file_names

        cases = os.listdir(root_dir)
        cases.sort()

        worklists = []
        for case in cases:
            file_dir_list = {k:False for k in checklist}

            for dirpath, dirnames, filenames in os.walk(os.path.join(root_dir, case)):
                for filename in filenames:
                    if filename in file_dir_list:
                        file_dir_list[filename] = os.path.join(dirpath, filename)
            
            if all(file_dir_list.values()):
                worklists.append({
                    'case_id':case, 
                    'mask_dir':file_dir_list[mask_file_name], 
                    'image_dirs':{image_name:file_dir_list[image_file_name] for image_name, image_file_name in zip(image_names, image_file_names)}
                    })
        
        self.worklists = worklists
        self.image_names = image_names

    def set_mask_filters(self, filters:Dict[str, Tuple]=None):
        if filters is not None:
            for key in filters.keys():
                assert key in self.image_names, f'filter key {key} not in images {self.image_names}'
            
            self.mask_filters = {k:v for k, v in filters.items()}

    def mask_modify(self, mask_arr, image_arrs, filters=None):
        if filters is None:
            filters = self.mask_filters

        mask_arr = mask_arr.astype(bool)

        for key, (lower, upper) in filters.items():
            lower_b = (image_arrs[key] > lower).astype(bool)
            upper_b = (image_arrs[key] < upper).astype(bool)

            mask_arr = mask_arr & lower_b & upper_b
    
        return mask_arr

    def _compute(self, worklist):
        case_id = worklist['case_id']
        mask_dir = worklist['mask_dir']
        image_dirs = worklist['image_dirs']

        mask = sitk.ReadImage(mask_dir)
        mask_arr = sitk.GetArrayFromImage(mask)

        output = {'case_id':case_id}
        image_arrs = {}
        for image_name, image_dir in image_dirs.items():
            image = sitk.ReadImage(image_dir)
            image_arr = sitk.GetArrayFromImage(image)
            image_arrs[image_name] = image_arr

        if self.mask_filters is not None:
            mask_arr = self.mask_modify(mask_arr, image_arrs)

        for image_name, image_arr in image_arrs.items():
            statistics = compute_statistics(image_arr, mask_arr, prefix=image_name, percentiles=self.percentiles, slice_statistics=self.slice_statistics)
            output.update(statistics)

        return output

    def run(self, cpus=1):
        def term(sig_num, addtion):
            print('Processor abort, being killed by SIGTERM')
            pool.terminate()
            pool.join()
            return None
        
        if cpus < 2:
            results = []
            for worklist in tqdm(self.worklists):
                # results.append(self._compute(worklist))
                try:
                    results.append(self._compute(worklist))
                except Exception as e:
                    print(f'error occured in {worklist}')
        else:
            NUM_OF_WORKERS = int(cpus)
            if NUM_OF_WORKERS < 1:
                NUM_OF_WORKERS = 1
            NUM_OF_WORKERS = min(cpu_count() - 1, NUM_OF_WORKERS)

            pool = Pool(NUM_OF_WORKERS)

            print("Main PID {0}".format(os.getpid()))

            signal.signal(signal.SIGTERM, term)

            try:
                results = pool.map_async(self._compute, self.worklists).get(888888)

            except (KeyboardInterrupt, SystemExit):
                print("...... Exit ......")
                pool.terminate()
                pool.join()
                return None
            else:
                print("......end......")
                pool.close()

            print("System exit")
            pool.join()

        result_df = pd.DataFrame(results)
        result_df.to_csv(os.path.join(self.output_dir, f'statistics_{time.time():.0f}.csv'), index=False)
