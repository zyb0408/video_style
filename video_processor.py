import cv2
import json
import numpy as np
import os
import subprocess
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QImage
import time


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
            'brightness': 0
        }
        # 使用时间戳创建唯一的临时文件名
        timestamp = int(time.time())
        self.temp_video_path = f'temp_video_{timestamp}.mp4'
        self.temp_audio_path = f'temp_audio_{timestamp}.aac'

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

    def adjust_image(self, frame):
        # 应用亮度和饱和度调整
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # 调整饱和度
        saturation_factor = 1 + (self.params['saturation'] / 100)
        hsv[:, :, 1] = hsv[:, :, 1] * saturation_factor
        hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
        
        # 调整亮度
        brightness_delta = int(self.params['brightness'] * 2.55)  # 将 -100~100 映射到 -255~255
        hsv[:, :, 2] = hsv[:, :, 2] + brightness_delta
        hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
        
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    def apply_style(self, frame):
        strength = self.params['strength'] / 100.0  # 将 0-100 转换为 0-1
        
        if self.style == '油画风格':
            sigma_s = int(60 * (1 + strength))
            sigma_r = 0.6 * strength
            styled = cv2.stylization(frame, sigma_s=sigma_s, sigma_r=sigma_r)
        elif self.style == '水彩风格':
            sigma_s = int(100 * (1 + strength))
            sigma_r = 0.3 * strength
            styled = cv2.stylization(frame, sigma_s=sigma_s, sigma_r=sigma_r)
        elif self.style == '卡通/动漫风格':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            kernel_size = int(9 * (1 + strength))
            if kernel_size % 2 == 0:
                kernel_size += 1
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                        cv2.THRESH_BINARY, kernel_size, kernel_size)
            color = cv2.bilateralFilter(frame, kernel_size, 300, 300)
            styled = cv2.bitwise_and(color, color, mask=edges)
        elif self.style == '素描风格':
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            inverted = 255 - gray
            kernel_size = int(21 * (1 + strength))
            if kernel_size % 2 == 0:
                kernel_size += 1
            blurred = cv2.GaussianBlur(inverted, (kernel_size, kernel_size), 0)
            inverted_blurred = 255 - blurred
            styled = cv2.divide(gray, inverted_blurred, scale=256.0)
        else:
            styled = frame

        if len(styled.shape) == 2:  # 如果是灰度图像，转换为BGR
            styled = cv2.cvtColor(styled, cv2.COLOR_GRAY2BGR)
            
        return styled

    def process_frame(self, frame):
        # 1. 先应用基础调整（亮度和饱和度）
        adjusted = self.adjust_image(frame)
        # 2. 再应用风格化效果
        return self.apply_style(adjusted)

    def process_video(self, output_path):
        """处理视频并直接保存到指定路径"""
        try:
            cap = cv2.VideoCapture(self.video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = 0
            frame_width = int(cap.get(3))
            frame_height = int(cap.get(4))
            fps = cap.get(cv2.CAP_PROP_FPS)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.temp_video_path, fourcc, fps, (frame_width, frame_height))

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                processed_frame = self.process_frame(frame)

                current_frame += 1
                progress = int((current_frame / frame_count) * 90)  # 视频处理占90%的进度
                self.progress_signal.emit(progress)

                # 发送预览帧
                height, width, channel = processed_frame.shape
                bytesPerLine = 3 * width
                qImg = QImage(processed_frame.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
                self.preview_frame_signal.emit(qImg)

                out.write(processed_frame)

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
                    # 如果合并失败，至少保留处理后的视频
                    import shutil
                    shutil.copy2(self.temp_video_path, output_path)
            else:
                # 如果没有音频，直接使用处理后的视频
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