import re
import os

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
    return sorted(files, key=natural_sort_key)

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
    Get list of manga directories within a root directory, sorted by natural order.
    
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
            
    # Sort using natural sort order (so '10巻' comes after '2巻' not before)
    return sorted(manga_dirs, key=natural_sort_key)
