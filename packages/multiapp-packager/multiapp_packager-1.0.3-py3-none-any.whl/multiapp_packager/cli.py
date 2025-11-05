#!/usr/bin/env python3
"""
多应用打包工具 - CLI 入口

职责：命令行参数解析和程序入口
"""
import os
import sys
import argparse
from .config_parser import ConfigParser
from .packager import Packager
from . import __version__


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="多应用打包工具（基于配置文件）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置文件 (multiapp_config.json)
  multiapp-packager

  # 指定配置文件
  multiapp-packager -c my_config.json

  # 指定输出目录
  multiapp-packager -o output/multiapps
        """
    )

    parser.add_argument(
        '-c', '--config',
        default='multiapp_config.json',
        help='配置文件路径 (默认: multiapp_config.json)'
    )

    parser.add_argument(
        '-o', '--output',
        default='multiapps',
        help='输出目录 (默认: multiapps)'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    args = parser.parse_args()

    # 解析配置文件
    print(f"{'='*60}")
    print(f"多应用打包工具")
    print(f"{'='*60}")

    config_file = args.config
    output_dir = args.output

    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"错误: 配置文件不存在: {config_file}")
        print(f"\n提示: 请创建配置文件或使用 -c 参数指定配置文件路径")
        return 1

    # 加载并解析配置
    apps = ConfigParser.load_and_parse(config_file)

    if not apps:
        print("错误: 没有找到有效的应用配置")
        return 1

    # 创建打包器并执行打包
    packager = Packager(output_dir=output_dir)
    success_count, fail_count = packager.package_all(apps)

    # 返回状态码
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
