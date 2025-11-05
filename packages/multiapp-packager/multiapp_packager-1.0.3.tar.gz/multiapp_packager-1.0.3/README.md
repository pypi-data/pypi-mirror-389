# 多应用打包工具

## 概述

这是一个基于配置文件的多应用打包工具，用于将编译好的应用打包成多应用格式。

## 特性

- ✅ **配置驱动**：通过 JSON 配置文件指定应用信息
- ✅ **多镜像支持**：单个应用可包含多个 bin 文件，分别烧录到不同地址
- ✅ **模块化设计**：清晰的职责分离
- ✅ **路径验证**：自动验证文件路径有效性
- ✅ **批量打包**：支持一次打包多个应用
- ✅ **灵活配置**：支持自定义输出目录
- ✅ **自动计算**：自动计算 MD5 和文件大小

## 目录结构

```
.
├── multiapps_pkg.py              # 主入口（CLI）
├── config_parser.py              # 配置文件解析器
├── app_info.py                   # 应用信息数据类
├── packager.py                   # 打包逻辑
└── multiapp_config.json          # 配置文件
```

## 配置文件格式

```json
{
  "version": "1.0",
  "description": "可选的描述信息",
  "apps": [
    {
      "app_name": "应用名称（必填）",
      "icon_path": "icon 图标路径（可选）",
      "description": "应用描述（可选）",
      "images": [
        {
          "bin_path": "bin 文件路径（必填）",
          "flash_addr": "Flash 烧录地址（必填）"
        }
      ]
    }
  ]
}
```

### 字段说明

#### 应用级字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `app_name` | string | ✅ | 应用名称，用作输出目录名 |
| `images` | array | ✅ | 镜像列表，至少包含一个镜像 |
| `icon_path` | string | ❌ | 应用图标 .png 文件路径 |
| `description` | string | ❌ | 应用描述信息 |

#### 镜像（images）字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `bin_path` | string | ✅ | 编译产物 .bin 文件的路径 |
| `flash_addr` | string | ✅ | Flash 烧录地址（十六进制，如 "0x100000"） |

### 配置示例

#### 单个 bin 文件

```json
{
  "app_name": "helloworld",
  "images": [
    {
      "bin_path": "build/helloworld.signed.bin",
      "flash_addr": "0x100000"
    }
  ]
}
```

#### 多个 bin 文件

```json
{
  "app_name": "lvgl_app",
  "icon_path": "app/icon.png",
  "description": "LVGL 应用（包含主程序和资源）",
  "images": [
    {
      "bin_path": "build/app.signed.bin",
      "flash_addr": "0x100000"
    },
    {
      "bin_path": "build/resources.bin",
      "flash_addr": "0x200000"
    },
    {
      "bin_path": "build/fonts.bin",
      "flash_addr": "0x300000"
    }
  ]
}
```

## 使用方法

### 1. 基本用法

使用默认配置文件 `multiapp_config.json`：

```bash
python multiapps_pkg.py
```

### 2. 指定配置文件

```bash
python multiapps_pkg.py -c my_config.json
```

## 输出结构

打包后会生成以下目录结构：

```
multiapps_switch/multiapps/
├── helloworld/
│   ├── config              # 应用配置文件（JSON）
│   ├── icon/
│   │   └── hello.png       # 应用图标
│   └── image/
│       └── helloworld.bin  # 应用二进制文件
├── lvgl_app/
│   ├── config
│   ├── icon/
│   │   └── lvgl.png
│   └── image/
│       ├── app.signed.bin      # 主程序
│       ├── resources.bin       # 资源文件
│       └── fonts.bin           # 字体文件
└── ...
```

### config 文件格式

#### 单个镜像

```json
{
  "version": "2.0",
  "app_name": "helloworld",
  "icon": {
    "file": "hello.png",
    "type": "png"
  },
  "image": [
    {
      "file": "helloworld.bin",
      "fmt": "raw",
      "md5": "a1b2c3d4e5f6...",
      "check": {
        "type": "none",
        "value": "0"
      },
      "copy_to": {
        "type": "nor",
        "addr": "0x100000",
        "size": "123456"
      }
    }
  ]
}
```

#### 多个镜像

```json
{
  "version": "2.0",
  "app_name": "lvgl_app",
  "icon": {
    "file": "lvgl.png",
    "type": "png"
  },
  "image": [
    {
      "file": "app.signed.bin",
      "fmt": "raw",
      "md5": "abc123...",
      "check": {
        "type": "none",
        "value": "0"
      },
      "copy_to": {
        "type": "nor",
        "addr": "0x100000",
        "size": "524288"
      }
    },
    {
      "file": "resources.bin",
      "fmt": "raw",
      "md5": "def456...",
      "check": {
        "type": "none",
        "value": "0"
      },
      "copy_to": {
        "type": "nor",
        "addr": "0x200000",
        "size": "1048576"
      }
    },
    {
      "file": "fonts.bin",
      "fmt": "raw",
      "md5": "789ghi...",
      "check": {
        "type": "none",
        "value": "0"
      },
      "copy_to": {
        "type": "nor",
        "addr": "0x300000",
        "size": "262144"
      }
    }
  ]
}
```

## 注意事项

1. **bin 文件必须存在**：工具不执行编译，需要先编译生成 .bin 文件
2. **icon 文件可选**：如果 icon 文件不存在，工具会使用默认配置继续打包
3. **Flash 地址**：确保不同镜像的 Flash 地址不重叠
4. **路径格式**：配置文件中的路径可以是相对路径或绝对路径

## 多 bin 文件使用场景

### 典型应用场景

1. **应用 + 资源分离**
   - 主程序 bin：应用代码
   - 资源 bin：图片、音频等资源文件
   - 字体 bin：字体文件

2. **固件 + 数据分离**
   - 固件 bin：核心程序
   - 配置 bin：配置数据
   - 用户数据 bin：用户数据区

3. **多阶段加载**
   - Bootloader bin：引导程序
   - 主应用 bin：主程序
   - OTA 备份 bin：备份区

### 配置示例

```json
{
  "app_name": "complex_app",
  "description": "复杂应用（主程序 + 资源）",
  "images": [
    {
      "bin_path": "build/app.signed.bin",
      "flash_addr": "0x100000"
    },
    {
      "bin_path": "build/resources.bin",
      "flash_addr": "0x200000"
    }
  ]
}
```

## 完整示例

参见 [`multiapp_config.json`](multiapp_config.json)
