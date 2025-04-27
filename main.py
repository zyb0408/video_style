import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QComboBox, QVBoxLayout, QWidget, QProgressBar, QLabel, QPushButton
from PySide6.QtCore import Qt, QThread
from video_processor import VideoProcessor, VideoProcessingThread
from PySide6.QtWidgets import QMessageBox


class VideoStylizationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initMenu()
        self.initStyleSelector()
        self.initProcessButton()
        self.initProgressBar()
        self.video_processor = None
        self.processing_thread = None
        self.selected_video_path = None

    def initUI(self):
        self.setWindowTitle('视频风格化GUI程序')
        self.setGeometry(100, 100, 800, 600)

    def initMenu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu('文件')
        open_action = file_menu.addAction('打开视频')
        open_action.triggered.connect(self.openVideoFile)

    def initStyleSelector(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        self.style_selector = QComboBox()
        self.style_selector.addItems(['油画风格', '水彩风格', '卡通/动漫风格', '素描风格', '复古滤镜', '自定义风格'])
        layout.addWidget(self.style_selector, alignment=Qt.AlignTop)
        central_widget.setLayout(layout)

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

    def openVideoFile(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter('视频文件 (*.mp4 *.avi *.mov)')
        if file_dialog.exec(): 
            file_path = file_dialog.selectedFiles()[0]
            print('选择的视频文件路径:', file_path)
            self.selected_video_path = file_path
            self.process_button.setEnabled(True)

    def onProcessButtonClicked(self):
        if self.selected_video_path:
            self.startVideoProcessing(self.selected_video_path)

    def startVideoProcessing(self, video_path):
        self.style_selector.setEnabled(False)
        self.process_button.setEnabled(False)
        style = self.style_selector.currentText()
        self.video_processor = VideoProcessor(video_path, style)
        self.processing_thread = VideoProcessingThread(self.video_processor)

        self.video_processor.progress_signal.connect(self.updateProgress)
        self.video_processor.finished_signal.connect(self.processingFinished)

        self.processing_thread.start()

    def updateProgress(self, progress):
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f'进度: {progress}%')

    def processingFinished(self):
        self.progress_bar.setValue(100)
        self.progress_label.setText('进度: 100%')
        print('视频处理完成')
        QMessageBox.information(self, '处理完成', '视频处理已完成！')
        self.style_selector.setEnabled(True)
        self.process_button.setEnabled(True)

    def closeEvent(self, event):
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoStylizationApp()
    window.show()
    sys.exit(app.exec())