import numpy as np
from scipy.ndimage import shift, rotate
from scipy.ndimage import affine_transform
def translate_3d(volume, dx=0, dy=0, dz=0):
    """
    平移三维图像：dx, dy, dz 分别为在 x, y, z 方向的偏移量（单位：像素）
    """
    return shift(volume, shift=(dz, dy, dx), mode='nearest')

def euler_angles_to_rotation_matrix(angles_deg, order='zxy'):
    """
    将欧拉角（单位：度）转换为旋转矩阵
    :param angles_deg: [α, β, γ]（绕 Z, X, Y 轴旋转的角度）
    :param order: 旋转顺序，例如 'zxy'
    :return: 3x3 旋转矩阵
    """
    alpha, beta, gamma = np.radians(angles_deg)

    def Rx(a): return np.array([[1, 0, 0],
                                [0, np.cos(a), -np.sin(a)],
                                [0, np.sin(a),  np.cos(a)]])
    def Ry(a): return np.array([[ np.cos(a), 0, np.sin(a)],
                                [0,          1, 0],
                                [-np.sin(a), 0, np.cos(a)]])
    def Rz(a): return np.array([[np.cos(a), -np.sin(a), 0],
                                [np.sin(a),  np.cos(a), 0],
                                [0,          0,         1]])

    if order == 'zxy':
        return Rz(alpha) @ Rx(beta) @ Ry(gamma)
    elif order == 'zyx':
        return Rz(alpha) @ Ry(beta) @ Rx(gamma)
    elif order == 'xyz':
        return Rx(alpha) @ Ry(beta) @ Rz(gamma)
    else:
        raise ValueError(f"Unsupported rotation order: {order}")

def rotate_3d(volume, angle=0, axes=(1, 2)):
    """
    沿给定轴对 volume 进行三维旋转（角度单位：度）
    默认绕 z 轴旋转（即 sagittal 和 coronal 面）
    """
    return rotate(volume, angle=angle, axes=axes, reshape=False, mode='nearest')

def rotate_3d_image(image, rotation_matrix, center=None):
    """
    应用旋转矩阵到 3D 图像（仿射变换）
    :param image: 3D numpy 数组
    :param rotation_matrix: 3x3 旋转矩阵
    :param center: 旋转中心坐标（默认为图像中心）
    :return: 旋转后的图像
    """
    if center is None:
        center = np.array(image.shape) // 2

    # 构建 4x4 仿射变换矩阵
    affine_mat = np.eye(4)
    affine_mat[:3, :3] = rotation_matrix
    affine_mat[:3, 3] = center - rotation_matrix @ center  # 平移补偿

    # 应用仿射变换
    rotated = affine_transform(
        image,
        matrix=affine_mat[:3, :3],
        offset=affine_mat[:3, 3],
        order=1,
        mode='constant',
        cval=0
    )
    return rotated