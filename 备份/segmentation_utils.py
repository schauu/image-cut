import numpy as np
from visualization import get_slice_image, numpy_to_vtk_image2d, render_image2d

def segment(ui, orientation, windowwide, windowlocation):
    array = ui._preprocessed_array
    if orientation == 'axial':
        val = ui.axialBar.value()
    elif orientation == 'sagittal':
        val = ui.sagittalBar.value()
    elif orientation == 'coronal':
        val = ui.coronalBar.value()
    else:
        return

    slice_array = get_slice_image(array, orientation, val)

    if windowwide is None:
        windowwide = 60
    if windowlocation is None:
        windowlocation = 230

    segmented_arr = np.zeros_like(slice_array, dtype=np.uint8)
    segmented_arr[(slice_array < (windowlocation + windowwide / 2)) &
                  (slice_array > (windowlocation - windowwide / 2))] = 255

    vtk_img = numpy_to_vtk_image2d(segmented_arr)

    if orientation == 'axial':
        render_image2d(vtk_img, ui.axialWidget, (1.0, 1.0))
    elif orientation == 'sagittal':
        render_image2d(vtk_img, ui.sagittalWidget, (1.0, 1.0))
    elif orientation == 'coronal':
        render_image2d(vtk_img, ui.coronalWidget, (1.0, 1.0))
