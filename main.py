#!/usr/bin/env python3
"""
マンガPDFビュアー メインモジュール
このモジュールはアプリケーションのエントリポイントです。
"""

import sys
from PyQt5.QtWidgets import QApplication
from manga_viewer import MangaViewer

def main():
    """アプリケーションのメインエントリポイント"""
    app = QApplication(sys.argv)
    
    # スタイルシートの設定（オプション）
    # app.setStyleSheet("""
    #     QPushButton { padding: 6px; }
    #     QLabel { margin: 2px; }
    # """)
    
    # メインウィンドウの作成と表示
    viewer = MangaViewer()
    viewer.show()
    
    # アプリケーションの実行
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
