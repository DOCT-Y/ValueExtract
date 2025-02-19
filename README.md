# ValueExtract
Extract values from registered multi-sequence images.

## introduction
This Python module is designed to extract histogram features (such as mean, standard deviation, percentiles, skewness, and kurtosis) from registered multi-sequence images, which are commonly encountered in diffusion imaging, such as the D, D*, and f maps in the IVIM model.

## Quick Start
see `main.py` file.
```python
from ValueExtract import ValueExtractor

if __name__ == '__main__': # must write this line when using multiple processes
    extractor = ValueExtractor(
        root_dir='path/to/your/image/folder', 
        output_dir='path/to/your/output/folder', 
        mask_file_name='IVIM-mask.nii.gz', 
        image_file_names={
            'D': 'D.nii.gz', 
            'D*': 'D-star.nii.gz', 
            'f': 'f.nii.gz', 
            }
        )
    extractor.set_mask_filters(filters={'f':[0, 1]})
    extractor.run(cpus=4)
```
Import the `ValueExtractor` from `ValueExtract` module, initialize the `ValueExtractor` object, and call `run` method. 

## API reference
### *class ValueExtract.ValueExtractor(root_dir:str, output_dir:str, mask_file_name:str, image_file_names:Dict[str, str], percentiles:List[int]=[5, 25, 50, 75, 95], slice_statistics:bool=False)*
+ **root_dir**: str. The path of the image folder. This folder should be structured like this:
```
root_dir_folder/
│── patient_1
│    ├── mask.nii.gz
│    ├── image_1.nii.gz
│    ├── image_2.nii.gz
│    └── image_n.nii.gz
│── patient_2
│    ├── mask.nii.gz
│    ├── image_1.nii.gz
│    ├── image_2.nii.gz
│    └── image_n.nii.gz
└── patient_n
     ├── mask.nii.gz
     ├── image_1.nii.gz
     ├── image_2.nii.gz
     └── image_n.nii.gz
```
+ **output_dir**: Str. The path where the extractor saves the result csv file.
+ **mask_file_name**: Str. The name of mask file (e.g., `mask.nii.gz`). Mask file format supported by `SimpleITK.ReadImage()` will be supported in this module. The mask should be a 3D array contains only 0 or 1.
+ **image_file_names**: Dict. Image names associated with file names in the form `{image_name: image_file_name}` (e.g., `{'modality_1':'image_1.nii.gz', 'modality_2':'image_2.nii.gz'}`). Image file format supported by `SimpleITK.ReadImage()` will be supported in this module. The image should be a 3D array that matches with the mask.
+ **percentiles**: List, default=[5, 25, 50, 75, 95]. List of percentiles to extract.
+ **slice_statistics**: Bool. Specifies if the features should be extracted slice by slice (i.e. 2D extraction).

### *ValueExtract.ValueExtractor.set_mask_filters(self, filters:Dict[str, Tuple]=None)*
Exclude outlier pixels from the mask. 
+ **filters**: Dict. Image names associated with the lower and upper boundary in the form `{image_name: (lowerb, upperb)}` (e.g., `{'modality_1': [0, 100], 'modality_2': [-1, 1]}`). Only lowerb < pixels < upperb will be included when extracting.
  
### *ValueExtract.ValueExtractor.run(self, cpus=1)*
Run extraction and save the result csv file.
+ **cups**: int, default=1. The number of processes for extraction. See [`multiprocessing.Pool`](https://docs.python.org/3/library/multiprocessing.html#multiprocessing.pool.Pool) for details.

### *test_if_match(root_dir:str, mask_file_name:str, image_file_names:Dict[str, str])*
Detect size mismatch between the mask and images.
+ **root_dir**: str. The path of the image folder. This folder should be structured like this:
```
root_dir_folder/
│── patient_1
│    ├── mask.nii.gz
│    ├── image_1.nii.gz
│    ├── image_2.nii.gz
│    └── image_n.nii.gz
│── patient_2
│    ├── mask.nii.gz
│    ├── image_1.nii.gz
│    ├── image_2.nii.gz
│    └── image_n.nii.gz
└── patient_n
     ├── mask.nii.gz
     ├── image_1.nii.gz
     ├── image_2.nii.gz
     └── image_n.nii.gz
```
+ **mask_file_name**: Str. The name of mask file (e.g., `mask.nii.gz`). Mask file format supported by `SimpleITK.ReadImage()` will be supported in this module. The mask should be a 3D array contains only 0 or 1.
+ **image_file_names**: Dict. Image names associated with file names in the form `{image_name: image_file_name}` (e.g., `{'modality_1':'image_1.nii.gz', 'modality_2':'image_2.nii.gz'}`). Image file format supported by `SimpleITK.ReadImage()` will be supported in this module. The image should be a 3D array that matches with the mask.

```python
from ValueExtract import test_if_match

if __name__ == '__main__': # must write this line when using multiple processes
    test_if_match(
        root_dir='path/to/your/image/folder', 
        mask_file_name='IVIM-mask.nii.gz', 
        image_file_names={
            'D': 'D.nii.gz', 
            'D*': 'D-star.nii.gz', 
            'f': 'f.nii.gz', 
            }
        )
```
