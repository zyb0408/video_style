import cv2
import json
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QImage


class VideoProcessor(QObject):
    progress_signal = Signal(int)
    finished_signal = Signal()
    preview_frame_signal = Signal(QImage)

    def __init__(self, video_path, style):
        super().__init__()
        self.video_path = video_path
        self.style = style

    def process_video(self):
        output_path = 'processed_video.mp4'
        cap = cv2.VideoCapture(self.video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        current_frame = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 这里可以添加不同风格的处理逻辑
            if self.style == '油画风格':
                processed_frame = cv2.stylization(frame, sigma_s=60, sigma_r=0.6)
            elif self.style == '水彩风格':
                processed_frame = cv2.stylization(frame, sigma_s=100, sigma_r=0.3)
            else:
                processed_frame = frame

            # 模拟进度更新
            current_frame += 1
            progress = int((current_frame / frame_count) * 100)
            self.progress_signal.emit(progress)

            # 发送预览帧
            height, width, channel = processed_frame.shape
            bytesPerLine = 3 * width
            qImg = QImage(processed_frame.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
            self.preview_frame_signal.emit(qImg)

            # 这里可以添加保存处理后视频的逻辑
            cap = cv2.VideoCapture(self.video_path)
            frame_width = int(cap.get(3))
            frame_height = int(cap.get(4))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, 20.0, (frame_width, frame_height))
            while cap.isOpened(): 
                ret, frame = cap.read()
                if ret:
                    # 这里添加风格处理逻辑
                    out.write(frame)
                else:
                    break
        output_path = 'processed_video.mp4'
        self.save_video(output_path)

        cap.release()
        out.release()
        print(f'视频已保存到 {output_path}')

        # 保存处理后的视频
        output_path = 'processed_video.mp4'
        self.save_video(output_path)

        cap.release()
        self.finished_signal.emit()

    def save_video(self, output_path):
        cap = cv2.VideoCapture(self.video_path)
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, 20.0, (frame_width, frame_height))

        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                # 这里添加风格处理逻辑
                if self.style == '油画风格':
                    frame = cv2.stylization(frame, sigma_s=60, sigma_r=0.6)
                elif self.style == '水彩风格':
                    frame = cv2.stylization(frame, sigma_s=100, sigma_r=0.3)
                out.write(frame)
            else:
                break

        cap.release()
        out.release()
        print(f'视频已保存到 {output_path}')


class VideoProcessingThread(QThread):
    def __init__(self, video_processor):
        super().__init__()
        self.video_processor = video_processor

    def run(self):
        self.video_processor.process_video()


def save_presets(presets, file_path='presets.json'):
    with open(file_path, 'w') as f:
        json.dump(presets, f)


def load_presets(file_path='presets.json'):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}