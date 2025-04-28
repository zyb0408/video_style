import cv2
import json
import numpy as np
import os
import subprocess
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QImage
import time
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed


class VideoProcessor(QObject):
    progress_signal = Signal(int)
    finished_signal = Signal()
    preview_frame_signal = Signal(QImage)

    def __init__(self, video_path, style, params=None):
        super().__init__()
        self.video_path = video_path
        self.style = style
        self.params = params or {
            'strength': 50,
            'saturation': 0,
            'brightness': 0,
            'scale_factor': 1.0  # 新增缩放参数
        }
        # 使用时间戳创建唯一的临时文件名
        timestamp = int(time.time())
        self.temp_video_path = f'temp_video_{timestamp}.mp4'
        self.temp_audio_path = f'temp_audio_{timestamp}.aac'
        
        # 检查是否支持 CUDA
        self.use_gpu = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if self.use_gpu:
            print("启用 GPU 加速")
        
        # 设置处理线程数
        self.num_workers = max(1, multiprocessing.cpu_count() - 1)

    def extract_audio(self, input_video, output_audio):
        """提取视频中的音频"""
        cmd = ['ffmpeg', '-i', input_video, '-vn', '-acodec', 'copy', output_audio, '-y']
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            print("音频提取失败")
            return False

    def merge_audio_video(self, video_path, audio_path, output_path):
        """合并视频和音频"""
        cmd = ['ffmpeg', '-i', video_path, '-i', audio_path, 
               '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
               output_path, '-y']
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            print("音视频合并失败")
            return False

    def cleanup_temp_files(self):
        """清理临时文件"""
        temp_files = [self.temp_video_path, self.temp_audio_path]
        for file in temp_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except Exception as e:
                    print(f"清理临时文件失败: {str(e)}")

    def resize_frame(self, frame, scale_factor):
        """调整帧的大小"""
        if scale_factor == 1.0:
            return frame
        width = int(frame.shape[1] * scale_factor)
        height = int(frame.shape[0] * scale_factor)
        if self.use_gpu:
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(frame)
            gpu_resized = cv2.cuda.resize(gpu_frame, (width, height))
            return gpu_resized.download()
        else:
            return cv2.resize(frame, (width, height))

    def process_frame_batch(self, frames):
        """处理一批帧"""
        processed_frames = []
        for frame in frames:
            # 调整大小
            frame = self.resize_frame(frame, self.params.get('scale_factor', 1.0))
            
            # 应用基础调整
            adjusted = self.adjust_image(frame)
            
            # 应用风格
            styled = self.apply_style(adjusted)
            
            processed_frames.append(styled)
        return processed_frames

    def adjust_image(self, frame):
        """应用亮度和饱和度调整"""
        if self.use_gpu:
            gpu_frame = cv2.cuda_GpuMat()
            gpu_frame.upload(frame)
            # 转换到 HSV 颜色空间
            gpu_hsv = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2HSV)
            hsv = gpu_hsv.download()
        else:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # 调整饱和度
        saturation_factor = 1 + (self.params['saturation'] / 100)
        hsv[:, :, 1] = hsv[:, :, 1] * saturation_factor
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        # 调整亮度
        brightness_delta = int(self.params['brightness'] * 2.55)
        hsv[:, :, 2] = hsv[:, :, 2] + brightness_delta
        hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
        
        if self.use_gpu:
            gpu_hsv = cv2.cuda_GpuMat()
            gpu_hsv.upload(hsv.astype(np.uint8))
            gpu_result = cv2.cuda.cvtColor(gpu_hsv, cv2.COLOR_HSV2BGR)
            return gpu_result.download()
        else:
            return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def apply_style(self, frame):
        """应用风格化效果"""
        strength = self.params['strength'] / 100.0
        
        if self.style == '油画风格':
            sigma_s = int(60 * (1 + strength))
            sigma_r = 0.6 * strength
            if self.use_gpu:
                gpu_frame = cv2.cuda_GpuMat()
                gpu_frame.upload(frame)
                gpu_result = cv2.cuda.stylization(gpu_frame)
                return gpu_result.download()
            else:
                return cv2.stylization(frame, sigma_s=sigma_s, sigma_r=sigma_r)
                
        elif self.style == '水彩风格':
            sigma_s = int(100 * (1 + strength))
            sigma_r = 0.3 * strength
            if self.use_gpu:
                gpu_frame = cv2.cuda_GpuMat()
                gpu_frame.upload(frame)
                gpu_result = cv2.cuda.stylization(gpu_frame)
                return gpu_result.download()
            else:
                return cv2.stylization(frame, sigma_s=sigma_s, sigma_r=sigma_r)
                
        elif self.style == '卡通/动漫风格':
            if self.use_gpu:
                gpu_frame = cv2.cuda_GpuMat()
                gpu_frame.upload(frame)
                gpu_gray = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2GRAY)
                gray = gpu_gray.download()
            else:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
            kernel_size = int(9 * (1 + strength))
            if kernel_size % 2 == 0:
                kernel_size += 1
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                        cv2.THRESH_BINARY, kernel_size, kernel_size)
            
            if self.use_gpu:
                gpu_edges = cv2.cuda_GpuMat()
                gpu_edges.upload(edges)
                gpu_color = cv2.cuda.bilateralFilter(gpu_frame, kernel_size, 300, 300)
                color = gpu_color.download()
            else:
                color = cv2.bilateralFilter(frame, kernel_size, 300, 300)
                
            return cv2.bitwise_and(color, color, mask=edges)
            
        elif self.style == '素描风格':
            # 获取原始图像的灰度版本
            if self.use_gpu:
                gpu_frame = cv2.cuda_GpuMat()
                gpu_frame.upload(frame)
                gpu_gray = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2GRAY)
                gray = gpu_gray.download()
            else:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 创建素描效果
            kernel_size = int(21 * (1 + strength))
            if kernel_size % 2 == 0:
                kernel_size += 1

            # 反转图像
            inverted = 255 - gray
            
            # 创建高斯模糊效果
            if self.use_gpu:
                gpu_inverted = cv2.cuda_GpuMat()
                gpu_inverted.upload(inverted)
                gpu_blurred = cv2.cuda.GaussianBlur(gpu_inverted, (kernel_size, kernel_size), 0)
                blurred = gpu_blurred.download()
            else:
                blurred = cv2.GaussianBlur(inverted, (kernel_size, kernel_size), 0)

            # 再次反转并进行除法运算
            inverted_blurred = 255 - blurred
            sketch = cv2.divide(gray, inverted_blurred, scale=256.0)

            # 增强对比度
            sketch = cv2.normalize(sketch, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
            
            # 将素描效果转换为3通道图像
            sketch_bgr = cv2.cvtColor(sketch.astype(np.uint8), cv2.COLOR_GRAY2BGR)
            
            # 可选：保持一些原始颜色信息
            if strength < 0.8:  # 当强度较低时，混合一些原始颜色
                alpha = 1 - strength  # 原始颜色的权重
                sketch_colored = cv2.addWeighted(frame, alpha, sketch_bgr, 1 - alpha, 0)
                return sketch_colored
            
            return sketch_bgr
        else:
            return frame

    def process_video(self, output_path):
        """处理视频并直接保存到指定路径"""
        try:
            cap = cv2.VideoCapture(self.video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = 0
            
            # 读取第一帧来确定输出视频的尺寸
            ret, first_frame = cap.read()
            if not ret:
                raise Exception("无法读取视频文件")
                
            # 计算缩放后的尺寸
            scale_factor = self.params.get('scale_factor', 1.0)
            frame_width = int(first_frame.shape[1] * scale_factor)
            frame_height = int(first_frame.shape[0] * scale_factor)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # 重置视频捕获器到开始位置
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            # 创建视频写入器，使用缩放后的尺寸
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.temp_video_path, fourcc, fps, (frame_width, frame_height))

            # 使用线程池处理帧
            batch_size = 10  # 每批处理的帧数
            frames_batch = []
            
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    frames_batch.append(frame)
                    current_frame += 1

                    # 当收集够一批帧或到达视频末尾时进行处理
                    if len(frames_batch) >= batch_size or current_frame == frame_count:
                        processed_frames = self.process_frame_batch(frames_batch)
                        
                        # 写入处理后的帧
                        for processed_frame in processed_frames:
                            # 确保帧的尺寸与输出视频尺寸匹配
                            if processed_frame.shape[:2] != (frame_height, frame_width):
                                processed_frame = cv2.resize(processed_frame, (frame_width, frame_height))
                            out.write(processed_frame)
                            
                        # 发送最后一帧作为预览
                        if processed_frames:
                            height, width = processed_frames[-1].shape[:2]
                            bytesPerLine = 3 * width
                            qImg = QImage(processed_frames[-1].data, width, height, 
                                        bytesPerLine, QImage.Format_RGB888).rgbSwapped()
                            self.preview_frame_signal.emit(qImg)
                        
                        # 更新进度
                        progress = int((current_frame / frame_count) * 90)
                        self.progress_signal.emit(progress)
                        
                        # 清空批次
                        frames_batch = []

            cap.release()
            out.release()

            # 提取音频
            self.progress_signal.emit(92)
            has_audio = self.extract_audio(self.video_path, self.temp_audio_path)
            
            # 合并音视频
            self.progress_signal.emit(95)
            if has_audio:
                success = self.merge_audio_video(self.temp_video_path, self.temp_audio_path, output_path)
                if not success:
                    import shutil
                    shutil.copy2(self.temp_video_path, output_path)
            else:
                import shutil
                shutil.copy2(self.temp_video_path, output_path)

            # 清理临时文件
            self.cleanup_temp_files()
            
            self.progress_signal.emit(100)
            print(f'视频已保存到 {output_path}')
            self.finished_signal.emit()

        except Exception as e:
            print(f"处理视频时出错: {str(e)}")
            self.cleanup_temp_files()
            raise e

    def save_video(self, output_path):
        """此方法不再需要，保留为空以保持接口兼容"""
        pass


class VideoProcessingThread(QThread):
    def __init__(self, video_processor, output_path):
        super().__init__()
        self.video_processor = video_processor
        self.output_path = output_path

    def run(self):
        self.video_processor.process_video(self.output_path)


def save_presets(presets, file_path='presets.json'):
    with open(file_path, 'w') as f:
        json.dump(presets, f)


def load_presets(file_path='presets.json'):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}