# マンガPDFビュアー

PDFフォーマットの漫画を閲覧するためのシンプルで軽量なビューワーアプリケーションです。漫画をフォルダごとに整理し、お気に入りとしおり機能で快適に読書を楽しめます。

## 特徴

- 階層化されたフォルダ構造で漫画を管理
- お気に入り機能で好きな漫画にすぐアクセス
- 自動的に最後に読んだページを記憶するしおり機能
- サムネイルプレビューで巻を素早く識別
- フルスクリーンモードでの快適な閲覧
- キーボードとマウスの操作設定のカスタマイズ
- 自動ページ送り機能

## インストール方法

### 必要条件

- Python 3.6以上
- PyQt5
- PyMuPDF (fitz)

### 依存パッケージのインストール

```bash
pip install PyQt5 PyMuPDF
```

### アプリケーションの実行

リポジトリをクローンして実行します：

```bash
git clone https://github.com/jokerjp1234/manga-pdf-viewer.git
cd manga-pdf-viewer
python main.py
```

## 使い方

1. 「漫画フォルダを本棚に追加」ボタンをクリックして漫画フォルダを追加します。
   - フォルダ構成は `漫画フォルダ/漫画タイトル/巻.pdf` を推奨します。
   - 例: `マンガ/ワンピース/01巻.pdf`, `マンガ/ワンピース/02巻.pdf`, など

2. 左側の本棚パネルで漫画を選択し、表示される巻一覧から読みたい巻を開きます。

3. ページナビゲーション：
   - 矢印キーでページ送り（左右または上下）
   - クリックでページ送り（設定で左右クリックの動作変更可能）
   - Home/Endキーで最初/最後のページに移動

4. お気に入り管理：
   - 「お気に入りに追加」ボタンで現在の漫画をお気に入りに追加
   - 「お気に入り」タブで登録済みの漫画にアクセス

5. しおり機能：
   - 自動的に最後に読んだページが記憶されます
   - 「しおり」タブで以前読んでいた漫画の続きから読めます

## アプリケーション構造

このアプリケーションは以下のコンポーネントで構成されています：

- `main.py` - アプリケーションのエントリポイント
- `manga_viewer.py` - メインウィンドウの実装
- `bookshelf.py` - 本棚、お気に入り、しおり管理機能
- `pdf_viewer.py` - PDFの表示と操作機能
- `thumbnail_loader.py` - サムネイルの非同期ロード処理
- `settings_manager.py` - アプリケーション設定の管理
- `utils.py` - ユーティリティ関数

## ライセンス

MITライセンス
