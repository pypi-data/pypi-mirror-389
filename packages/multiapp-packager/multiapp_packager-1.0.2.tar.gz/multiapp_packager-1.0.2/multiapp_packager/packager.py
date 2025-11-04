"""
应用打包器

职责：将应用文件打包成多应用格式
"""
import os
import shutil
import json
import hashlib
from typing import Optional
from .app_info import AppInfo


class Packager:
    """应用打包器"""

    def __init__(self, output_dir: str = 'multiapps'):
        """
        初始化打包器

        :param output_dir: 输出目录
        """
        self.output_dir = output_dir

    def package(self, app_info: AppInfo) -> bool:
        """
        打包单个应用

        :param app_info: 应用信息对象
        :return: 是否打包成功
        """
        print(f"\n{'='*60}")
        print(f"开始打包应用: {app_info.app_name}")
        print(f"{'='*60}")

        # 验证路径
        is_valid, errors = app_info.validate_paths()
        if not is_valid:
            for error in errors:
                print(f"错误: {error}")
            return False

        try:
            # 创建应用目录
            app_output_dir = self._create_app_directory(app_info.app_name)

            # 处理所有 bin 文件
            image_configs = self._process_binaries(app_info, app_output_dir)

            # 处理 icon 文件
            icon_filename = self._process_icon(app_info, app_output_dir)

            # 生成配置文件
            self._generate_config(app_info, app_output_dir, image_configs, icon_filename)

            print(f"✓ 应用 {app_info.app_name} 打包成功")
            print(f"  输出目录: {app_output_dir}")
            return True

        except Exception as e:
            print(f"✗ 打包应用 {app_info.app_name} 时出错: {e}")
            return False

    def package_all(self, apps: list[AppInfo]) -> tuple[int, int]:
        """
        批量打包应用

        :param apps: 应用信息列表
        :return: (成功数量, 失败数量)
        """
        success_count = 0
        fail_count = 0

        print(f"\n准备打包 {len(apps)} 个应用...")

        for app_info in apps:
            if self.package(app_info):
                success_count += 1
            else:
                fail_count += 1

        print(f"\n{'='*60}")
        print(f"打包完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        print(f"{'='*60}")

        return success_count, fail_count

    def _create_app_directory(self, app_name: str) -> str:
        """
        创建应用输出目录结构

        :param app_name: 应用名称
        :return: 应用输出目录路径
        """
        # 创建主输出目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 创建应用目录
        app_dir = os.path.join(self.output_dir, app_name)
        os.makedirs(app_dir, exist_ok=True)

        # 创建子目录
        os.makedirs(os.path.join(app_dir, 'icon'), exist_ok=True)
        os.makedirs(os.path.join(app_dir, 'image'), exist_ok=True)

        return app_dir

    def _process_binaries(self, app_info: AppInfo, app_output_dir: str) -> list[dict]:
        """
        处理所有二进制文件

        :param app_info: 应用信息
        :param app_output_dir: 应用输出目录
        :return: 镜像配置列表
        """
        image_configs = []

        print(f"  处理 {len(app_info.images)} 个镜像文件:")
        for idx, image in enumerate(app_info.images, 1):
            bin_filename = image.get_filename()
            src_path = image.bin_path
            dst_path = os.path.join(app_output_dir, 'image', bin_filename)

            # 复制文件
            shutil.copy(src_path, dst_path)
            print(f"    [{idx}] 复制: {src_path} -> {dst_path}")

            # 计算 MD5 和文件大小
            md5 = self._calculate_md5(dst_path)
            size = image.get_size()
            print(f"        MD5: {md5}")
            print(f"        地址: {image.flash_addr}, 大小: {size} 字节")

            # 构建镜像配置
            image_configs.append({
                "file": bin_filename,
                "fmt": "raw",
                "md5": md5,
                "check": {
                    "type": "none",
                    "value": "0"
                },
                "copy_to": {
                    "type": "nor",
                    "addr": image.flash_addr,
                    "size": str(size)
                }
            })

        return image_configs

    def _process_icon(self, app_info: AppInfo, app_output_dir: str) -> Optional[str]:
        """
        处理图标文件

        :param app_info: 应用信息
        :param app_output_dir: 应用输出目录
        :return: icon 文件名（如果有）
        """
        if not app_info.icon_path:
            print(f"  ⚠ 未指定 icon 文件，使用默认配置")
            return "default.png"

        # 检查 icon 文件是否存在
        if not os.path.exists(app_info.icon_path):
            print(f"  ⚠ icon 文件不存在: {app_info.icon_path}")
            print(f"  ⚠ 将使用默认配置")
            return "default.png"

        icon_filename = app_info.get_icon_filename()
        src_path = app_info.icon_path
        dst_path = os.path.join(app_output_dir, 'icon', icon_filename)

        shutil.copy(src_path, dst_path)
        print(f"  ✓ 复制 icon 文件: {src_path} -> {dst_path}")

        return icon_filename

    def _generate_config(self, app_info: AppInfo, app_output_dir: str,
                        image_configs: list[dict], icon_filename: str):
        """
        生成配置文件

        :param app_info: 应用信息
        :param app_output_dir: 应用输出目录
        :param image_configs: 镜像配置列表
        :param icon_filename: icon 文件名
        """
        config_content = {
            "version": "2.0",
            "app_name": app_info.app_name,
            "icon": {
                "file": icon_filename,
                "type": "png"
            },
            "image": image_configs
        }

        config_path = os.path.join(app_output_dir, 'config')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_content, f, indent=4, ensure_ascii=False)

        print(f"  ✓ 生成配置文件: {config_path}")

    @staticmethod
    def _calculate_md5(file_path: str) -> str:
        """
        计算文件 MD5

        :param file_path: 文件路径
        :return: MD5 值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
