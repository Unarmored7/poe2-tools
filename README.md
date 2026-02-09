# poe2-tools

Path of Exile 2 游戏辅助工具集，包含自动喝药、装备洗练、模板匹配等功能。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 功能模块

- **自动喝药** (`auto_potion`) - 监控血条/蓝条，自动按键喝药
- **装备洗练** (`reforge`) - 图像识别自动洗练装备
- **模板匹配** (`template_matcher`) - 主词条/T阶图标匹配测试
- **AI装备检查** (`ai_inspector`) - 使用 DashScope OCR+LLM 判断装备

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 项目结构

```
poe2-tools/
├── main.py                 # 程序入口
├── config/                 # 配置文件目录
├── poe2_tools/             # 主功能模块包
│   ├── app.py              # 主应用类
│   ├── auto_potion.py      # 自动喝药
│   ├── reforge.py          # 装备洗练
│   ├── template_matcher.py # 模板匹配
│   ├── ai_inspector.py     # AI装备检查
│   └── utils/              # 公共工具
└── templates/              # 模板图片目录
```

## 致谢

本项目基于 [zaozi/poe2-c](https://github.com/zaozi/poe2-c) 二次开发，感谢原作者的贡献。

## License

MIT License - 详见 [LICENSE](LICENSE) 文件
