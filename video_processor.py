import cv2
import json
from PySide6.QtCore import QObject, Signal, QThread


class VideoProcessor(QObject):
    progress_signal = Signal(int)
    finished_signal = Signal()

    def __init__(self, video_path, style):
        super().__init__()
        self.video_path = video_path
        self.style = style

    def process_video(self):
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

            # 这里可以添加保存处理后视频的逻辑
            def save_video(self, output_path):
                # 这里添加实际的视频保存逻辑
                print(f'视频已保存到 {output_path}')

        cap.release()
        self.finished_signal.emit()


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