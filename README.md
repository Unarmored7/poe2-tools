# poe2-tools

Path of Exile 2 辅助工具集（Python + Tkinter）。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 功能

- 自动喝药（血条/蓝条阈值触发 + 定时触发）
- 混沌石洗炼（按词条块与命中组数判定）
- 神圣石洗炼（全词条综合阈值 / 指定词条块模式）
- 全局热键 `F12` 开始/停止（运行时可自动最小化，停止后恢复窗口）

## 环境要求

- Python `3.10+`
- Windows（鼠标/键盘自动操作逻辑按 Windows 使用习惯实现）

## 安装

```bash
pip install -r requirements.txt
pip install -e .
```

## 启动

```bash
python main.py
```

或：

```bash
python -m poe2_tools
```

## 使用说明

### 自动喝药

1. 设置血条/蓝条区域
2. 配置阈值、按键、检测间隔（可选定时喝药）
3. 启动监控

### 混沌石洗炼

1. 设置混沌石坐标和装备坐标
2. 添加目标词条块（支持复合词条多行）
3. 设置命中条数并启动

### 神圣石洗炼

1. 设置神圣石坐标和装备坐标
2. 选择模式：全词条综合 / 指定词条块
3. 设置阈值并启动

## 自动打包（GitHub Actions）

项目已提供工作流：`.github/workflows/build-release.yml`

- 手动触发：执行构建并上传 `artifact`
- 推送 `v*` 标签：自动构建 `POE2-Tools.exe` 并上传到 GitHub Release

## 项目结构

```text
poe2-tools/
├── .github/workflows/build-release.yml
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
├── assets/
├── config/
├── templates/
└── src/
    └── poe2_tools/
        ├── __init__.py
        ├── __main__.py
        ├── app.py
        ├── auto_potion.py
        ├── reforge.py
        ├── theme.py
        ├── ai_inspector.py
        └── utils/
```

## 注意事项

- 本项目会进行鼠标/键盘自动操作，请先在测试环境校准坐标与参数
- 使用辅助工具可能违反游戏服务条款，请自行评估与承担风险

## 参考项目

- https://github.com/regulus001z/PoE2-Auto-Crafter
- https://github.com/zaozi/poe2-c

## License

MIT License，详见 [LICENSE](LICENSE)
