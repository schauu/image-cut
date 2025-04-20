import SimpleITK as sitk
import numpy as np

def read_dicom_series(folder, return_numpy=True):
    reader = sitk.ImageSeriesReader()
    reader.MetaDataDictionaryArrayUpdateOn()
    reader.LoadPrivateTagsOn()

    series_IDs = reader.GetGDCMSeriesIDs(folder)
    if not series_IDs:
        raise RuntimeError("未找到 DICOM 序列")

    file_names = reader.GetGDCMSeriesFileNames(folder, series_IDs[0])
    reader.SetFileNames(file_names)

    image = reader.Execute()
    array = sitk.GetArrayFromImage(image)

    # 读取第一个切片的全部 DICOM tag
    full_info = {}
    keys = reader.GetMetaDataKeys(0)
    for key in keys:
        value = reader.GetMetaData(0, key)
        full_info[key] = value

    # 构造中文标签（可选）
    tag_map = {
        "0010|0010": "患者姓名",
        "0010|0020": "患者ID",
        "0008|0060": "成像模态",
        "0008|0020": "检查日期",
        "0008|1030": "检查描述",
        "0020|000D": "Study UID",
        "0028|0010": "图像行数",
        "0028|0011": "图像列数",
        "0028|0030": "像素间距",
        "0028|0100": "位深"
    }

    basic_info = {}
    for tag, label in tag_map.items():
        basic_info[label] = full_info.get(tag, "(无)")

    metadata = {
        "基本信息": basic_info,
        "全部DICOM标签": full_info  # ✅ 添加所有标签
    }

    if return_numpy:
        return image, array, metadata
    else:
        return image
