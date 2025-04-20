import vtk
import numpy as np
from vtk.util import numpy_support
import SimpleITK as sitk


def get_slice_image(array, orientation, index=None):
    z, y, x = array.shape
    if orientation == 'axial':
        index = z // 2 if index is None else np.clip(index, 0, z - 1)
        return array[index, :, :]
    elif orientation == 'coronal':
        index = y // 2 if index is None else np.clip(index, 0, y - 1)
        return array[:, index, :]
    elif orientation == 'sagittal':
        index = x // 2 if index is None else np.clip(index, 0, x - 1)
        return array[:, :, index]
    else:
        raise ValueError("Invalid orientation")


def preprocess_array(array):
    array = np.clip(array, np.percentile(array, 1), np.percentile(array, 99))
    array = (array - array.min()) / (array.max() - array.min()) * 255
    return array.astype(np.uint8)


def numpy_to_vtk_image2d(slice_array):
    height, width = slice_array.shape
    flat_array = slice_array.flatten(order="C")
    vtk_data_array = numpy_support.numpy_to_vtk(
        num_array=flat_array, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
    image = vtk.vtkImageData()
    image.SetDimensions(width, height, 1)
    image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
    image.GetPointData().SetScalars(vtk_data_array)
    return image


def render_image2d(image_2d, vtk_widget, spacing=(1.0, 1.0), reset_camera=False):
    mapper = vtk.vtkImageSliceMapper()
    mapper.SetInputData(image_2d)
    actor = vtk.vtkImageSlice()
    actor.SetMapper(mapper)
    actor.SetScale(spacing[0], spacing[1], 1.0)
    renderer = vtk.vtkRenderer()
    renderer.AddViewProp(actor)
    if reset_camera:
        renderer.ResetCamera()
    renderer.SetBackground(0, 0, 0)
    vtk_widget.GetRenderWindow().GetRenderers().RemoveAllItems()
    vtk_widget.GetRenderWindow().AddRenderer(renderer)
    vtk_widget.GetRenderWindow().Render()


def update_status_bar(ui, axial_idx=None, sagittal_idx=None, coronal_idx=None):
    a_max = ui.axialBar.maximum() + 1
    s_max = ui.sagittalBar.maximum() + 1
    c_max = ui.coronalBar.maximum() + 1
    a_val = axial_idx if axial_idx is not None else ui.axialBar.value()
    s_val = sagittal_idx if sagittal_idx is not None else ui.sagittalBar.value()
    c_val = coronal_idx if coronal_idx is not None else ui.coronalBar.value()
    ui.status_bar.showMessage(f"Axial: {a_val+1}/{a_max} | Sagittal: {s_val+1}/{s_max} | Coronal: {c_val+1}/{c_max}")


class ScrollSliceInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self, orientation, array, ui, sitk_image, spacing=(1.0, 1.0)):
        super().__init__()
        self.orientation = orientation
        self.array = array
        self.ui = ui
        self.image = sitk_image
        self.spacing = spacing
        self.z, self.y, self.x = array.shape
        self.index = {
            'axial': self.z // 2,
            'sagittal': self.x // 2,
            'coronal': self.y // 2
        }[orientation]
        self.max_index = {
            'axial': self.z - 1,
            'sagittal': self.x - 1,
            'coronal': self.y - 1
        }[orientation]
        self.AddObserver("MouseWheelForwardEvent", self.scroll_up)
        self.AddObserver("MouseWheelBackwardEvent", self.scroll_down)

    def scroll_up(self, obj, event):
        if self.index < self.max_index:
            self.index += 1
            update_slice(self.array, self.ui, self.orientation, self.index, sitk_image=self.image, update_status=False)
            bar = {'axial': self.ui.axialBar, 'sagittal': self.ui.sagittalBar, 'coronal': self.ui.coronalBar}[self.orientation]
            bar.blockSignals(True)
            bar.setValue(self.index)
            bar.blockSignals(False)
            update_status_bar(self.ui)
            self.ui.controller.update_histogram(slider=self.orientation, index=self.index)

    def scroll_down(self, obj, event):
        if self.index > 0:
            self.index -= 1
            update_slice(self.array, self.ui, self.orientation, self.index, sitk_image=self.image, update_status=False)
            bar = {'axial': self.ui.axialBar, 'sagittal': self.ui.sagittalBar, 'coronal': self.ui.coronalBar}[self.orientation]
            bar.blockSignals(True)
            bar.setValue(self.index)
            bar.blockSignals(False)
            update_status_bar(self.ui)
            self.ui.controller.update_histogram(slider=self.orientation, index=self.index)


def update_slice(array, ui, orientation, index, sitk_image=None, update_status=False):
    array = ui._preprocessed_array
    slice_array = get_slice_image(array, orientation, index)
    vtk_img = numpy_to_vtk_image2d(slice_array)
    sx, sy, sz = sitk_image.GetSpacing() if sitk_image else (1.0, 1.0, 1.0)
    spacing = {'axial': (sx, sy), 'sagittal': (sy, sz), 'coronal': (sx, sz)}[orientation]
    render_func = {'axial': ui.axialWidget, 'sagittal': ui.sagittalWidget, 'coronal': ui.coronalWidget}[orientation]
    render_image2d(vtk_img, render_func, spacing)
    if update_status:
        update_status_bar(ui)

def show_views_with_slider(array, ui, sitk_image=None):
    array = preprocess_array(array)
    ui._preprocessed_array = array

    z, y, x = array.shape
    ui.axialBar.setMaximum(z - 1)
    ui.sagittalBar.setMaximum(x - 1)
    ui.coronalBar.setMaximum(y - 1)

    ui.axialBar.setValue(z // 2)
    ui.sagittalBar.setValue(x // 2)
    ui.coronalBar.setValue(y // 2)

    if sitk_image:
        sx, sy, sz = sitk_image.GetSpacing()
    else:
        sx, sy, sz = 1.0, 1.0, 1.0

    spacing_axial = (sx, sy)
    spacing_sagittal = (sy, sz)
    spacing_coronal = (sx, sz)

    # 初次显示
    render_image2d(numpy_to_vtk_image2d(get_slice_image(array, 'axial')), ui.axialWidget, spacing_axial, reset_camera=True)
    render_image2d(numpy_to_vtk_image2d(get_slice_image(array, 'sagittal')), ui.sagittalWidget, spacing_sagittal, reset_camera=True)
    render_image2d(numpy_to_vtk_image2d(get_slice_image(array, 'coronal')), ui.coronalWidget, spacing_coronal, reset_camera=True)

    # 设置默认交互器样式（非测量模式）
    style_axial = ScrollSliceInteractorStyle("axial", array, ui, sitk_image, spacing_axial)
    style_sagittal = ScrollSliceInteractorStyle("sagittal", array, ui, sitk_image, spacing_sagittal)
    style_coronal = ScrollSliceInteractorStyle("coronal", array, ui, sitk_image, spacing_coronal)

    ui.axialWidget.GetRenderWindow().GetInteractor().SetInteractorStyle(style_axial)
    ui.sagittalWidget.GetRenderWindow().GetInteractor().SetInteractorStyle(style_sagittal)
    ui.coronalWidget.GetRenderWindow().GetInteractor().SetInteractorStyle(style_coronal)

    ui.axialWidget.GetRenderWindow().GetInteractor().Initialize()
    ui.sagittalWidget.GetRenderWindow().GetInteractor().Initialize()
    ui.coronalWidget.GetRenderWindow().GetInteractor().Initialize()



class MeasurementInteractorStyle(vtk.vtkInteractorStyleImage):
    def __init__(self, orientation, array, ui, spacing=(1.0, 1.0), renderer=None):
        super().__init__()
        self.orientation = orientation
        self.array = array
        self.ui = ui
        self.spacing = spacing
        self.renderer = renderer
        self.start = None
        self.temp_actor = None

        self.AddObserver("LeftButtonPressEvent", self.on_click)
        self.AddObserver("MouseMoveEvent", self.on_move)
        self.AddObserver("RightButtonPressEvent", self.on_reset)

    def on_click(self, obj, event):
        interactor = self.GetInteractor()
        pos = interactor.GetEventPosition()
        picker = vtk.vtkPropPicker()
        renderer = self.renderer

        if not renderer:
            print("[测量错误] 渲染器未准备好")
            return
        picker.Pick(pos[0], pos[1], 0, renderer)
        p = picker.GetPickPosition()

        if p == (0.0, 0.0, 0.0) or any(np.isnan(p)):
            print("[测量错误] 未能成功拾取点")
            return

        if self.start is None:
            self.start = p
        else:
            self.draw_measurement(self.start, p)
            self.start = None
            self.remove_temp_line()

    def on_move(self, obj, event):
        if self.start is None:
            return
        interactor = self.GetInteractor()
        pos = interactor.GetEventPosition()
        picker = vtk.vtkPropPicker()
        picker.Pick(pos[0], pos[1], 0, self.renderer)
        p = picker.GetPickPosition()
        if any(np.isnan(p)):
            return
        self.draw_temp_line(self.start, p)

    def on_reset(self, obj, event):
        self.start = None
        self.remove_temp_line()

    def draw_temp_line(self, p1, p2):
        self.remove_temp_line()
        line = vtk.vtkLineSource()
        line.SetPoint1(p1)
        line.SetPoint2(p2)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(line.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1, 0, 0)
        actor.GetProperty().SetLineWidth(1)
        self.renderer.AddActor(actor)
        self.temp_actor = actor
        self.GetInteractor().GetRenderWindow().Render()

    def remove_temp_line(self):
        if self.temp_actor:
            self.renderer.RemoveActor(self.temp_actor)
            self.temp_actor = None
            self.GetInteractor().GetRenderWindow().Render()

    def draw_measurement(self, p1, p2):
        if any(np.isnan(p1)) or any(np.isnan(p2)):
            print("[测量错误] 坐标无效")
            return
        line = vtk.vtkLineSource()
        line.SetPoint1(p1)
        line.SetPoint2(p2)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(line.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0, 1, 0)
        actor.GetProperty().SetLineWidth(2)

        dx = (p1[0] - p2[0])
        dy = (p1[1] - p2[1])
        dist = np.sqrt(dx ** 2 + dy ** 2)

        label = vtk.vtkTextActor()
        label.SetInput(f"{dist:.2f} mm")
        label.GetTextProperty().SetFontSize(16)
        label.GetTextProperty().SetColor(1, 1, 0)
        label.SetPosition((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)

        renderer = self.renderer

        if renderer:
            renderer.AddActor(actor)
            renderer.AddActor(label)
            self.GetInteractor().GetRenderWindow().Render()


def enable_measurement(ui, enabled, sitk_image):
    if not hasattr(ui, "_preprocessed_array") or ui._preprocessed_array is None:
        return

    array = ui._preprocessed_array
    if sitk_image:
        sx, sy, sz = sitk_image.GetSpacing()
    else:
        sx, sy, sz = 1.0, 1.0, 1.0

    configs = [
        ("axial", ui.axialWidget, (sx, sy)),
        ("sagittal", ui.sagittalWidget, (sy, sz)),
        ("coronal", ui.coronalWidget, (sx, sz)),
    ]

    for orientation, widget, spacing in configs:
        interactor = widget.GetRenderWindow().GetInteractor()
        renderers = widget.GetRenderWindow().GetRenderers()

        # ✅ 修复关键：强制确保 renderer 不为空
        if renderers.GetNumberOfItems() == 0:
            fallback_renderer = vtk.vtkRenderer()
            widget.GetRenderWindow().AddRenderer(fallback_renderer)
            widget.GetRenderWindow().Render()

        renderer = widget.GetRenderWindow().GetRenderers().GetFirstRenderer()
        if enabled:
            style = MeasurementInteractorStyle(orientation, array, ui, spacing, renderer=renderer)
        else:
            style = ScrollSliceInteractorStyle(orientation, array, ui, sitk_image, spacing)

        interactor.SetInteractorStyle(style)
        interactor.Initialize()

