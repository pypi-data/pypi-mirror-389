"""
配置文件解析器

职责：读取和解析 multiapp_config.json 配置文件
"""
import json
import os
from typing import List
from .app_info import AppInfo, ImageInfo


class ConfigParser:
    """配置文件解析器"""

    def __init__(self, config_file: str):
        """
        初始化解析器

        :param config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config_data = None

    def load(self) -> bool:
        """
        加载配置文件

        :return: 是否加载成功
        """
        if not os.path.exists(self.config_file):
            print(f"错误: 配置文件不存在: {self.config_file}")
            return False

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            print(f"成功加载配置文件: {self.config_file}")
            return True
        except json.JSONDecodeError as e:
            print(f"错误: 配置文件 JSON 格式错误: {e}")
            return False
        except Exception as e:
            print(f"错误: 读取配置文件失败: {e}")
            return False

    def parse(self) -> List[AppInfo]:
        """
        解析配置文件，返回应用信息列表

        :return: AppInfo 对象列表
        """
        if not self.config_data:
            print("错误: 配置文件未加载")
            return []

        if 'apps' not in self.config_data:
            print("错误: 配置文件中缺少 'apps' 字段")
            return []

        apps = []
        for idx, app_config in enumerate(self.config_data['apps']):
            try:
                app_info = self._parse_app_config(app_config)
                apps.append(app_info)
            except ValueError as e:
                print(f"警告: 跳过第 {idx + 1} 个应用配置，原因: {e}")
            except Exception as e:
                print(f"警告: 解析第 {idx + 1} 个应用配置时出错: {e}")

        print(f"成功解析 {len(apps)} 个应用配置")
        return apps

    def _parse_app_config(self, app_config: dict) -> AppInfo:
        """
        解析单个应用配置

        :param app_config: 应用配置字典
        :return: AppInfo 对象
        """
        # 必填字段
        if 'app_name' not in app_config:
            raise ValueError("缺少必填字段: app_name")
        if 'images' not in app_config:
            raise ValueError("缺少必填字段: images")

        # 解析 images 列表
        images = []
        for idx, image_config in enumerate(app_config['images']):
            if 'bin_path' not in image_config:
                raise ValueError(f"镜像 {idx + 1} 缺少必填字段: bin_path")
            if 'flash_addr' not in image_config:
                raise ValueError(f"镜像 {idx + 1} 缺少必填字段: flash_addr")

            images.append(ImageInfo(
                bin_path=image_config['bin_path'],
                flash_addr=image_config['flash_addr']
            ))

        # 创建 AppInfo 对象
        app_info = AppInfo(
            app_name=app_config['app_name'],
            images=images,
            icon_path=app_config.get('icon_path'),
            description=app_config.get('description', '')
        )

        return app_info

    def get_version(self) -> str:
        """获取配置文件版本"""
        if self.config_data and 'version' in self.config_data:
            return self.config_data['version']
        return 'unknown'

    @staticmethod
    def load_and_parse(config_file: str) -> List[AppInfo]:
        """
        便捷方法：加载并解析配置文件

        :param config_file: 配置文件路径
        :return: AppInfo 对象列表
        """
        parser = ConfigParser(config_file)
        if parser.load():
            return parser.parse()
        return []
