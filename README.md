# 视频风格化处理工具

一个基于 PySide6 和 OpenCV 的视频风格化处理工具，支持多种艺术风格转换，包括油画、水彩、卡通/动漫和素描风格。

## 主要功能

- **多种艺术风格转换**

  - 油画风格：模拟油画笔触效果
  - 水彩风格：实现水彩画效果
  - 卡通/动漫风格：将视频转换为卡通/动漫风格
  - 素描风格：将视频转换为素描效果

- **视频处理参数调整**

  - 强度调整：控制风格化效果的强度
  - 饱和度调整：调整视频的饱和度
  - 亮度调整：调整视频的亮度
  - 视频尺寸缩放：支持 25%-100% 的尺寸调整

- **性能优化**

  - GPU 加速：支持 NVIDIA GPU 加速处理
  - 多线程处理：利用多核 CPU 进行并行处理
  - 批量处理：优化内存使用，提高处理效率

- **用户友好的界面**
  - 实时预览：处理过程中实时显示效果
  - 进度显示：清晰显示处理进度
  - 参数预设：支持保存和加载参数预设

## 技术栈

- **前端框架**：PySide6 (Qt for Python)
- **图像处理**：OpenCV (支持 CUDA 加速)
- **视频处理**：FFmpeg
- **并行处理**：Python multiprocessing, concurrent.futures
- **依赖管理**：pip

## 系统要求

- Python 3.8 或更高版本
- OpenCV 4.5.0 或更高版本（支持 CUDA）
- FFmpeg
- PySide6
- 推荐使用 NVIDIA GPU 以获得更好的性能

## 安装步骤

1. 克隆项目到本地：

```bash
git clone [项目地址]
cd video_style
```

2. 创建并激活虚拟环境（推荐）：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 安装 FFmpeg：

- MacOS (使用 Homebrew)：

```bash
brew install ffmpeg
```

- Ubuntu/Debian：

```bash
sudo apt-get install ffmpeg
```

- Windows：
  从 [FFmpeg 官网](https://ffmpeg.org/download.html) 下载并添加到系统环境变量

## 使用方法

1. 启动程序：

```bash
python main.py
```

2. 基本操作：

   - 点击"选择视频"按钮选择要处理的视频文件
   - 在参数面板调整处理参数
   - 选择输出路径
   - 点击"开始处理"按钮开始处理
   - 处理完成后，视频将保存到指定位置

3. 参数说明：

   - 强度：控制风格化效果的强度（0-100）
   - 饱和度：调整视频的饱和度（-100 到 100）
   - 亮度：调整视频的亮度（-100 到 100）
   - 视频尺寸：调整输出视频的尺寸（25%-100%）

4. 性能优化建议：
   - 使用 GPU 加速：确保系统安装了支持 CUDA 的 OpenCV
   - 调整视频尺寸：降低视频尺寸可以显著提高处理速度
   - 使用参数预设：保存常用参数组合，方便快速应用

## 注意事项

- 处理大视频文件时，请确保有足够的磁盘空间
- 使用 GPU 加速时，请确保显卡驱动和 CUDA 工具包已正确安装
- 处理过程中请勿关闭程序，否则可能导致处理中断
- 建议在处理前先使用较小的视频进行测试

## 许可证

[待定]
