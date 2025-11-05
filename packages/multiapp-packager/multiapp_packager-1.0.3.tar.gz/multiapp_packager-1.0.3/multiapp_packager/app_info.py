"""
应用信息数据类

职责：封装应用的元数据信息
"""
import os
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ImageInfo:
    """镜像信息数据类（单个 bin 文件）"""
    bin_path: str
    flash_addr: str

    def __post_init__(self):
        """验证必填字段"""
        if not self.bin_path:
            raise ValueError("bin_path 不能为空")
        if not self.flash_addr:
            raise ValueError("flash_addr 不能为空")

    def validate_path(self) -> tuple[bool, Optional[str]]:
        """
        验证文件路径是否存在

        :return: (是否有效, 错误信息)
        """
        if not os.path.exists(self.bin_path):
            return False, f"bin 文件不存在: {self.bin_path}"
        return True, None

    def get_filename(self) -> str:
        """获取文件名"""
        return os.path.basename(self.bin_path)

    def get_size(self) -> int:
        """获取文件大小"""
        return os.path.getsize(self.bin_path)

    def __repr__(self) -> str:
        return f"ImageInfo(bin_path='{self.bin_path}', flash_addr='{self.flash_addr}')"


@dataclass
class AppInfo:
    """应用信息数据类"""
    app_name: str
    images: List[ImageInfo]
    icon_path: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        """验证必填字段"""
        if not self.app_name:
            raise ValueError("app_name 不能为空")
        if not self.images or len(self.images) == 0:
            raise ValueError("至少需要一个 image 配置")

    def validate_paths(self) -> tuple[bool, list[str]]:
        """
        验证所有文件路径是否存在
        注意：icon 文件不存在不会导致验证失败，只会打印警告

        :return: (是否全部有效, 错误信息列表)
        """
        errors = []

        # 检查所有 bin 文件（必须存在）
        for idx, image in enumerate(self.images):
            is_valid, error = image.validate_path()
            if not is_valid:
                errors.append(f"镜像 {idx + 1}: {error}")

        # icon 文件不存在只是警告，不影响打包
        # 在 packager 中处理

        return len(errors) == 0, errors

    def get_icon_filename(self) -> Optional[str]:
        """获取 icon 文件名"""
        if self.icon_path:
            return os.path.basename(self.icon_path)
        return None

    def __repr__(self) -> str:
        return (f"AppInfo(app_name='{self.app_name}', "
                f"images={len(self.images)} 个镜像)")
