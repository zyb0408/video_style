import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QComboBox, QVBoxLayout, QWidget, QProgressBar, QLabel, QPushButton, QHBoxLayout, QSlider, QGroupBox, QFormLayout
from PySide6.QtCore import Qt, QThread, QUrl
from PySide6.QtGui import QPixmap # 导入QPixmap
from video_processor import VideoProcessor, VideoProcessingThread
from PySide6.QtWidgets import QMessageBox
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtMultimedia import QMediaPlayer


class VideoStylizationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initMenu()
        self.initFileControls()  # 新增文件控制区域
        self.initStyleSelector()
        self.original_media_player = QMediaPlayer()
        self.processed_media_player = QMediaPlayer()
        self.initPreviewWidgets()
        self.initParamsPanel()
        self.initProcessButton()
        self.initProgressBar()
        self.video_processor = None
        self.processing_thread = None
        self.selected_video_path = None
        self.output_video_path = None

    def initUI(self):
        self.setWindowTitle('视频风格化GUI程序')
        self.setGeometry(100, 100, 800, 600)

    def initMenu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        open_action = file_menu.addAction('打开视频')
        open_action.triggered.connect(self.openVideoFile)

    def initFileControls(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # 创建文件控制区域
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout()
        
        # 输入视频选择
        input_layout = QHBoxLayout()
        self.input_path_label = QLabel("未选择视频文件")
        self.input_path_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        select_button = QPushButton("选择视频文件")
        select_button.clicked.connect(self.openVideoFile)
        input_layout.addWidget(self.input_path_label, stretch=1)
        input_layout.addWidget(select_button)
        file_layout.addLayout(input_layout)
        
        # 输出路径选择
        output_layout = QHBoxLayout()
        self.output_path_label = QLabel("未设置输出路径")
        self.output_path_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        output_button = QPushButton("设置输出路径")
        output_button.clicked.connect(self.setOutputPath)
        output_layout.addWidget(self.output_path_label, stretch=1)
        output_layout.addWidget(output_button)
        file_layout.addLayout(output_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        central_widget.setLayout(layout)

    def initStyleSelector(self):
        central_widget = self.centralWidget()
        layout = central_widget.layout()
        
        # 创建风格选择组
        style_group = QGroupBox("风格选择")
        style_layout = QVBoxLayout()
        
        self.style_selector = QComboBox()
        self.style_selector.addItems(['油画风格', '水彩风格', '卡通/动漫风格', '素描风格', '复古滤镜', '自定义风格'])
        style_layout.addWidget(self.style_selector)
        
        style_group.setLayout(style_layout)
        layout.addWidget(style_group)

    def initPreviewWidgets(self):
        central_widget = self.centralWidget()
        layout = central_widget.layout()

        # 创建左右预览窗口
        self.original_preview = QVideoWidget()
        self.processed_preview = QVideoWidget()

        # 设置媒体播放器与预览窗口关联
        self.original_media_player.setVideoOutput(self.original_preview)
        self.processed_media_player.setVideoOutput(self.processed_preview)

        # 创建水平布局放置两个预览窗口
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(self.original_preview)
        preview_layout.addWidget(self.processed_preview)

        # 将预览布局添加到主布局
        layout.addLayout(preview_layout)

    def initParamsPanel(self):
        central_widget = self.centralWidget()
        layout = central_widget.layout()
        
        # 创建参数调节组
        params_group = QGroupBox("参数调节")
        params_layout = QFormLayout()
        
        # 创建强度滑块
        self.strength_slider = QSlider(Qt.Horizontal)
        self.strength_slider.setRange(0, 100)
        self.strength_slider.setValue(50)
        self.strength_label = QLabel("50%")
        self.strength_slider.valueChanged.connect(
            lambda v: self.strength_label.setText(f"{v}%"))
        params_layout.addRow("效果强度:", self.strength_slider)
        params_layout.addRow("", self.strength_label)
        
        # 创建饱和度滑块
        self.saturation_slider = QSlider(Qt.Horizontal)
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)
        self.saturation_label = QLabel("0")
        self.saturation_slider.valueChanged.connect(
            lambda v: self.saturation_label.setText(str(v)))
        params_layout.addRow("饱和度:", self.saturation_slider)
        params_layout.addRow("", self.saturation_label)
        
        # 创建亮度滑块
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_label = QLabel("0")
        self.brightness_slider.valueChanged.connect(
            lambda v: self.brightness_label.setText(str(v)))
        params_layout.addRow("亮度:", self.brightness_slider)
        params_layout.addRow("", self.brightness_label)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

    def initProcessButton(self):
        self.process_button = QPushButton('开始处理视频', self)
        self.process_button.clicked.connect(self.onProcessButtonClicked)
        self.process_button.setEnabled(False)
        central_widget = self.centralWidget()
        layout = central_widget.layout()
        layout.addWidget(self.process_button)

    def initProgressBar(self):
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel('进度: 0%')
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.statusBar().addPermanentWidget(self.progress_label)

    def setOutputPath(self):
        file_dialog = QFileDialog()
        output_path, _ = file_dialog.getSaveFileName(
            self, 
            '设置输出视频路径', 
            '', 
            '视频文件 (*.mp4)'
        )
        if output_path:
            self.output_video_path = output_path
            self.output_path_label.setText(output_path)
            self.updateProcessButton()

    def openVideoFile(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter('视频文件 (*.mp4 *.avi *.mov)')
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.selected_video_path = file_path
            self.input_path_label.setText(file_path)
            self.original_media_player.setSource(QUrl.fromLocalFile(file_path))
            self.original_media_player.play()
            self.updateProcessButton()

    def updateProcessButton(self):
        # 只有当输入和输出路径都设置后才启用处理按钮
        self.process_button.setEnabled(
            bool(self.selected_video_path and self.output_video_path)
        )

    def onProcessButtonClicked(self):
        if self.selected_video_path and self.output_video_path:
            self.startVideoProcessing(self.selected_video_path)

    def startVideoProcessing(self, video_path):
        self.style_selector.setEnabled(False)
        self.process_button.setEnabled(False)
        style = self.style_selector.currentText()
        # 检查是否选择了支持的风格
        supported_styles = ['油画风格', '水彩风格', '卡通/动漫风格', '素描风格', '复古滤镜', '自定义风格']
        if style not in supported_styles:
            QMessageBox.warning(self, '警告', '所选风格暂不支持，请重新选择。')
            self.style_selector.setEnabled(True)
            self.process_button.setEnabled(True)
            return
            
        # 获取参数值
        params = {
            'strength': self.strength_slider.value(),
            'saturation': self.saturation_slider.value(),
            'brightness': self.brightness_slider.value()
        }
        
        self.video_processor = VideoProcessor(video_path, style, params)
        self.processing_thread = VideoProcessingThread(self.video_processor)

        self.video_processor.progress_signal.connect(self.updateProgress)
        self.video_processor.finished_signal.connect(self.processingFinished)
        self.video_processor.preview_frame_signal.connect(self.showProcessedPreview)

        # 使用预设的输出路径
        self.processing_thread.start()
        self.video_processor.process_video(self.output_video_path)

    def updateProgress(self, progress):
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f'进度: {progress}%')

    def processingFinished(self):
        self.progress_bar.setValue(100)
        self.progress_label.setText('进度: 100%')
        print('视频处理完成')
        QMessageBox.information(self, '处理完成', f'视频已保存到：\n{self.output_video_path}')
        self.style_selector.setEnabled(True)
        self.process_button.setEnabled(True)

    def closeEvent(self, event):
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(self, '确认退出', 
                                       '视频正在处理中，确定要退出吗？',
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.processing_thread.terminate()
                self.processing_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def showProcessedPreview(self, frame):
        # 转换 QImage 为 QPixmap
        pixmap = QPixmap.fromImage(frame)
        # 创建一个 QLabel 用于显示预览
        if not hasattr(self, 'processed_preview_label'):
            self.processed_preview_label = QLabel(self.processed_preview)
            self.processed_preview_label.setAlignment(Qt.AlignCenter)
        # 设置缩放后的 Pixmap 到 QLabel
        scaled_pixmap = pixmap.scaled(self.processed_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.processed_preview_label.setPixmap(scaled_pixmap)
        self.processed_preview_label.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoStylizationApp()
    window.show()
    sys.exit(app.exec())