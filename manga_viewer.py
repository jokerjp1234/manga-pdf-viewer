import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QSplitter, QAction, QToolBar, QMessageBox, 
                           QDialog, QLineEdit, QInputDialog, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QIcon

from settings_manager import SettingsManager
from bookshelf import Bookshelf
from pdf_viewer import PDFViewer

class MangaViewer(QMainWindow):
    """
    メインアプリケーションウィンドウ。すべてのコンポーネントを統合する。
    """
    
    def __init__(self):
        """メインウィンドウの初期化。"""
        super().__init__()
        
        # 設定の初期化
        self.settings_manager = SettingsManager()
        
        # ウィンドウプロパティの設定
        self.setWindowTitle("マンガPDFビュアー")
        self.resize(1200, 800)
        
        # インスタンス変数の初期化
        self.auto_turn_timer = QTimer()
        self.auto_turn_timer.timeout.connect(self.auto_turn_page)
        self.is_fullscreen = False
        self.pre_fullscreen_splitter_sizes = None
        
        # UIのセットアップ
        self.setup_ui()
        
        # 接続のセットアップ
        self.setup_connections()
        
        # メニューバーとツールバーのセットアップ
        self.create_menu_bar()
        self.create_toolbar()
    
    def setup_ui(self):
        """ユーザーインターフェースのセットアップ。"""
        # セントラルウィジェット
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # 本棚とPDFビューワーのためのスプリッター
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # 本棚コンポーネント
        self.bookshelf = Bookshelf(self.settings_manager)
        
        # PDFビューワーコンポーネント
        self.pdf_viewer = PDFViewer(self.settings_manager)
        
        # スプリッターにコンポーネントを追加
        self.splitter.addWidget(self.bookshelf)
        self.splitter.addWidget(self.pdf_viewer)
        self.splitter.setSizes([300, 900])  # デフォルトの分割サイズ
    
    def setup_connections(self):
        """コンポーネント間のシグナル接続のセットアップ。"""
        # 本棚シグナルをハンドラーに接続
        self.bookshelf.volume_selected.connect(self.on_volume_selected)
    
    def on_volume_selected(self, manga_name, manga_path, volume_name):
        """
        本棚からの巻選択を処理する。
        
        引数:
            manga_name: 選択された漫画の名前
            manga_path: 漫画ディレクトリへのパス
            volume_name: 巻ファイルの名前
        """
        # ビューワーでPDFを読み込む
        self.pdf_viewer.load_pdf(manga_name, manga_path, volume_name)
    
    def create_menu_bar(self):
        """アプリケーションメニューバーの作成。"""
        menu_bar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menu_bar.addMenu("ファイル")
        
        open_action = QAction("漫画フォルダを追加", self)
        open_action.triggered.connect(self.bookshelf.add_manga_folder)
        file_menu.addAction(open_action)
        
        exit_action = QAction("終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 表示メニュー
        view_menu = menu_bar.addMenu("表示")
        
        self.fullscreen_action = QAction("フルスクリーン", self)
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.fullscreen_action)
        
        fit_window_action = QAction("ウィンドウに合わせる", self)
        fit_window_action.setCheckable(True)
        fit_window_action.setChecked(self.pdf_viewer.fit_to_window)
        fit_window_action.triggered.connect(self.pdf_viewer.toggle_fit_to_window)
        view_menu.addAction(fit_window_action)
        
        # ツールメニュー
        tools_menu = menu_bar.addMenu("ツール")
        
        bookmark_action = QAction("しおりを追加", self)
        bookmark_action.triggered.connect(self.add_bookmark)
        tools_menu.addAction(bookmark_action)
        
        auto_turn_action = QAction("自動ページ送り", self)
        auto_turn_action.triggered.connect(self.set_auto_turn)
        tools_menu.addAction(auto_turn_action)
        
        # 設定メニュー
        settings_menu = menu_bar.addMenu("設定")
        
        mouse_settings_action = QAction("マウス操作設定", self)
        mouse_settings_action.triggered.connect(self.configure_mouse)
        settings_menu.addAction(mouse_settings_action)
        
        self.keyboard_settings_action = QAction("キーボード操作設定", self)
        self.keyboard_settings_action.triggered.connect(self.configure_keyboard)
        settings_menu.addAction(self.keyboard_settings_action)
        
        # キーボード設定アクションのテキスト初期設定
        self.update_keyboard_action_text()
    
    def create_toolbar(self):
        """ツールバーの作成。"""
        toolbar = QToolBar("メインツールバー")
        self.addToolBar(toolbar)
        
        open_action = QAction("漫画フォルダを追加", self)
        open_action.triggered.connect(self.bookshelf.add_manga_folder)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        bookmark_action = QAction("しおりを追加", self)
        bookmark_action.triggered.connect(self.add_bookmark)
        toolbar.addAction(bookmark_action)
        
        toolbar.addSeparator()
        
        fit_window_action = QAction("ウィンドウに合わせる", self)
        fit_window_action.setCheckable(True)
        fit_window_action.setChecked(self.pdf_viewer.fit_to_window)
        fit_window_action.triggered.connect(self.pdf_viewer.toggle_fit_to_window)
        toolbar.addAction(fit_window_action)
        
        self.fullscreen_toolbar_action = QAction("フルスクリーン", self)
        self.fullscreen_toolbar_action.triggered.connect(self.toggle_fullscreen)
        toolbar.addAction(self.fullscreen_toolbar_action)
        
        auto_turn_action = QAction("自動ページ送り", self)
        auto_turn_action.triggered.connect(self.set_auto_turn)
        toolbar.addAction(auto_turn_action)
    
    def toggle_fullscreen(self):
        """フルスクリーン表示の切り替え。"""
        if self.is_fullscreen:
            # フルスクリーン解除
            self.showNormal()
            self.is_fullscreen = False
            self.fullscreen_action.setChecked(False)
            # 左パネルを再表示
            self.bookshelf.show()
            # スプリッタサイズを元に戻す
            if self.pre_fullscreen_splitter_sizes:
                self.splitter.setSizes(self.pre_fullscreen_splitter_sizes)
        else:
            # フルスクリーン表示
            # 現在のスプリッタサイズを保存
            self.pre_fullscreen_splitter_sizes = self.splitter.sizes()
            # 左パネルを非表示
            self.bookshelf.hide()
            # フルスクリーン表示
            self.showFullScreen()
            self.is_fullscreen = True
            self.fullscreen_action.setChecked(True)
        
        # PDFページをリロードして適切なサイズに調整
        if self.pdf_viewer.pdf_document:
            self.pdf_viewer.display_page()
    
    def add_bookmark(self):
        """現在のページにしおりを追加。"""
        if not self.pdf_viewer.current_manga or not self.pdf_viewer.current_volume:
            QMessageBox.information(self, "情報", "マンガと巻を選択してください。")
            return
        
        # 現在のページにしおりを追加
        self.settings_manager.add_bookmark(
            self.pdf_viewer.current_manga,
            self.pdf_viewer.current_volume,
            self.pdf_viewer.current_page
        )
        
        # 本棚のしおりリストを更新
        self.bookshelf.update_bookmarks_list()
        
        QMessageBox.information(
            self, 
            "しおり", 
            f"{self.pdf_viewer.current_manga} - {self.pdf_viewer.current_volume}の{self.pdf_viewer.current_page + 1}ページ目にしおりを追加しました。"
        )
    
    def set_auto_turn(self):
        """自動ページ送りの設定。"""
        if self.auto_turn_timer.isActive():
            self.auto_turn_timer.stop()
            QMessageBox.information(self, "自動ページ送り", "自動ページ送りを停止しました。")
            return
        
        seconds, ok = QInputDialog.getInt(
            self, "自動ページ送り", "ページ送りの間隔を設定してください（秒）：",
            10, 1, 60, 1
        )
        
        if ok:
            self.auto_turn_timer.start(seconds * 1000)
            QMessageBox.information(
                self, 
                "自動ページ送り", 
                f"自動ページ送りを開始しました。間隔: {seconds}秒"
            )
    
    def auto_turn_page(self):
        """自動ページ送りの実行。"""
        self.pdf_viewer.next_page()
    
    def configure_mouse(self):
        """マウス操作の設定。"""
        dialog = QDialog(self)
        dialog.setWindowTitle("マウス操作設定")
        layout = QVBoxLayout(dialog)
        
        # 現在の設定を取得
        left_click_next = self.settings_manager.get_setting("left_click_next", True)
        
        def toggle_mouse_behavior(checked):
            self.settings_manager.set_setting("left_click_next", checked)
            # PDFビューワーの設定を更新
            self.pdf_viewer.left_click_next = checked
        
        # 通常の動作
        normal_button = QPushButton("左クリック：次のページ / 右クリック：前のページ")
        normal_button.setCheckable(True)
        normal_button.setChecked(left_click_next)
        normal_button.clicked.connect(lambda: toggle_mouse_behavior(True))
        layout.addWidget(normal_button)
        
        # 逆の動作
        reverse_button = QPushButton("左クリック：前のページ / 右クリック：次のページ")
        reverse_button.setCheckable(True)
        reverse_button.setChecked(not left_click_next)
        reverse_button.clicked.connect(lambda: toggle_mouse_behavior(False))
        layout.addWidget(reverse_button)
        
        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec_()
    
    def configure_keyboard(self):
        """キーボード操作の設定。"""
        dialog = QDialog(self)
        dialog.setWindowTitle("キーボード操作設定")
        layout = QVBoxLayout(dialog)
        
        # 現在の設定を取得
        use_arrow_keys = self.settings_manager.get_setting("use_arrow_keys", True)
        
        # 現在の状態に基づいてボタンのテキストを設定
        button_text = "矢印キーでページ送りを無効にする" if use_arrow_keys else "矢印キーでページ送りを有効にする"
        keyboard_check = QPushButton(button_text)
        keyboard_check.setCheckable(True)
        keyboard_check.setChecked(use_arrow_keys)
        
        def toggle_keyboard(checked):
            self.settings_manager.set_setting("use_arrow_keys", checked)
            # PDFビューワーの設定を更新
            self.pdf_viewer.use_arrow_keys = checked
            # メニューアクションのテキストも更新
            self.update_keyboard_action_text()
            
            if checked:
                keyboard_check.setText("矢印キーでページ送りを無効にする")
            else:
                keyboard_check.setText("矢印キーでページ送りを有効にする")
        
        keyboard_check.clicked.connect(toggle_keyboard)
        layout.addWidget(keyboard_check)
        
        info_label = QLabel("左右の矢印キーでページ送り、Home/Endキーで最初/最後のページに移動できます")
        layout.addWidget(info_label)
        
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec_()
    
    def update_keyboard_action_text(self):
        """キーボード設定アクションのテキストを更新。"""
        use_arrow_keys = self.settings_manager.get_setting("use_arrow_keys", True)
        if hasattr(self, 'keyboard_settings_action'):
            if use_arrow_keys:
                self.keyboard_settings_action.setText("キーボード操作設定を無効にする")
            else:
                self.keyboard_settings_action.setText("キーボード操作設定を有効にする")
    
    def closeEvent(self, event):
        """アプリケーション終了時の処理。"""
        # PDFドキュメントを閉じる
        self.pdf_viewer.close_document()
        
        # イベントを受け入れる
        event.accept()
