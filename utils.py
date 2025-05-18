import re
import os
import unicodedata

def natural_sort_key(s):
    """
    Sort strings containing numbers in a natural way.
    E.g. ["file1.pdf", "file10.pdf", "file2.pdf"] will be sorted as 
    ["file1.pdf", "file2.pdf", "file10.pdf"] instead of 
    ["file1.pdf", "file10.pdf", "file2.pdf"]
    
    Args:
        s: String to get sort key for
        
    Returns:
        List to be used as sort key
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def japanese_sort_key(s):
    """
    Sort strings in Japanese alphabetical order (あいうえお order).
    Converts Japanese characters to romaji for sorting.
    
    Args:
        s: String to get sort key for
        
    Returns:
        String to be used as sort key
    """
    # Convert to lowercase and normalize
    s = s.lower()
    
    # For strings with numbers, use natural sort first
    if any(c.isdigit() for c in s):
        return natural_sort_key(s)
    
    # For Japanese strings, convert to romaji
    normalized = unicodedata.normalize('NFKC', s)
    
    # Map hiragana/katakana to their position in the Japanese alphabet
    # This is a very simplified approach - for a more accurate sort,
    # you might want to use a dedicated Japanese language library
    japanese_char_order = {
        # あ行
        'あ': 'a01', 'い': 'a02', 'う': 'a03', 'え': 'a04', 'お': 'a05',
        'ぁ': 'a01', 'ぃ': 'a02', 'ぅ': 'a03', 'ぇ': 'a04', 'ぉ': 'a05',
        # か行
        'か': 'b01', 'き': 'b02', 'く': 'b03', 'け': 'b04', 'こ': 'b05',
        'が': 'b06', 'ぎ': 'b07', 'ぐ': 'b08', 'げ': 'b09', 'ご': 'b10',
        # さ行
        'さ': 'c01', 'し': 'c02', 'す': 'c03', 'せ': 'c04', 'そ': 'c05',
        'ざ': 'c06', 'じ': 'c07', 'ず': 'c08', 'ぜ': 'c09', 'ぞ': 'c10',
        # た行
        'た': 'd01', 'ち': 'd02', 'つ': 'd03', 'て': 'd04', 'と': 'd05',
        'だ': 'd06', 'ぢ': 'd07', 'づ': 'd08', 'で': 'd09', 'ど': 'd10',
        'っ': 'd03',
        # な行
        'な': 'e01', 'に': 'e02', 'ぬ': 'e03', 'ね': 'e04', 'の': 'e05',
        # は行
        'は': 'f01', 'ひ': 'f02', 'ふ': 'f03', 'へ': 'f04', 'ほ': 'f05',
        'ば': 'f06', 'び': 'f07', 'ぶ': 'f08', 'べ': 'f09', 'ぼ': 'f10',
        'ぱ': 'f11', 'ぴ': 'f12', 'ぷ': 'f13', 'ぺ': 'f14', 'ぽ': 'f15',
        # ま行
        'ま': 'g01', 'み': 'g02', 'む': 'g03', 'め': 'g04', 'も': 'g05',
        # や行
        'や': 'h01', 'ゆ': 'h02', 'よ': 'h03',
        'ゃ': 'h01', 'ゅ': 'h02', 'ょ': 'h03',
        # ら行
        'ら': 'i01', 'り': 'i02', 'る': 'i03', 'れ': 'i04', 'ろ': 'i05',
        # わ行
        'わ': 'j01', 'を': 'j02', 'ん': 'j03',
        'ゎ': 'j01',
        
        # カタカナ (same order as hiragana)
        # ア行
        'ア': 'a01', 'イ': 'a02', 'ウ': 'a03', 'エ': 'a04', 'オ': 'a05',
        'ァ': 'a01', 'ィ': 'a02', 'ゥ': 'a03', 'ェ': 'a04', 'ォ': 'a05',
        # カ行
        'カ': 'b01', 'キ': 'b02', 'ク': 'b03', 'ケ': 'b04', 'コ': 'b05',
        'ガ': 'b06', 'ギ': 'b07', 'グ': 'b08', 'ゲ': 'b09', 'ゴ': 'b10',
        # サ行
        'サ': 'c01', 'シ': 'c02', 'ス': 'c03', 'セ': 'c04', 'ソ': 'c05',
        'ザ': 'c06', 'ジ': 'c07', 'ズ': 'c08', 'ゼ': 'c09', 'ゾ': 'c10',
        # タ行
        'タ': 'd01', 'チ': 'd02', 'ツ': 'd03', 'テ': 'd04', 'ト': 'd05',
        'ダ': 'd06', 'ヂ': 'd07', 'ヅ': 'd08', 'デ': 'd09', 'ド': 'd10',
        'ッ': 'd03',
        # ナ行
        'ナ': 'e01', 'ニ': 'e02', 'ヌ': 'e03', 'ネ': 'e04', 'ノ': 'e05',
        # ハ行
        'ハ': 'f01', 'ヒ': 'f02', 'フ': 'f03', 'ヘ': 'f04', 'ホ': 'f05',
        'バ': 'f06', 'ビ': 'f07', 'ブ': 'f08', 'ベ': 'f09', 'ボ': 'f10',
        'パ': 'f11', 'ピ': 'f12', 'プ': 'f13', 'ペ': 'f14', 'ポ': 'f15',
        # マ行
        'マ': 'g01', 'ミ': 'g02', 'ム': 'g03', 'メ': 'g04', 'モ': 'g05',
        # ヤ行
        'ヤ': 'h01', 'ユ': 'h02', 'ヨ': 'h03',
        'ャ': 'h01', 'ュ': 'h02', 'ョ': 'h03',
        # ラ行
        'ラ': 'i01', 'リ': 'i02', 'ル': 'i03', 'レ': 'i04', 'ロ': 'i05',
        # ワ行
        'ワ': 'j01', 'ヲ': 'j02', 'ン': 'j03',
        'ヮ': 'j01',
    }
    
    # For each character in the string
    result = []
    for char in normalized:
        # For Japanese characters, use our mapping
        if char in japanese_char_order:
            result.append(japanese_char_order[char])
        else:
            # For other characters, use the character itself
            result.append(char)
            
    return ''.join(result)

def get_pdf_files(directory):
    """
    Get list of PDF files in a directory, sorted in natural order.
    
    Args:
        directory: Directory to search for PDF files
        
    Returns:
        List of PDF filenames
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return []
        
    files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    return sorted(files, key=japanese_sort_key)

def is_valid_manga_directory(directory):
    """
    Check if a directory is a valid manga directory (contains PDFs).
    
    Args:
        directory: Directory to check
        
    Returns:
        Boolean indicating if it's a valid manga directory
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return False
        
    for f in os.listdir(directory):
        if f.lower().endswith('.pdf'):
            return True
            
    return False
    
def get_manga_directories(root_directory):
    """
    Get list of manga directories within a root directory, sorted by Japanese order.
    
    Args:
        root_directory: Root directory to search
        
    Returns:
        List of valid manga directory names
    """
    if not os.path.exists(root_directory) or not os.path.isdir(root_directory):
        return []
        
    manga_dirs = []
    for d in os.listdir(root_directory):
        full_path = os.path.join(root_directory, d)
        if os.path.isdir(full_path) and is_valid_manga_directory(full_path):
            manga_dirs.append(d)
            
    # Sort using Japanese sort key
    return sorted(manga_dirs, key=japanese_sort_key)
