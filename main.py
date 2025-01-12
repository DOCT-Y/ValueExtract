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