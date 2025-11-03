"""
heapgeneratorq - A comprehensive collection of algorithms and data structures
"""

__version__ = "0.1.0"
__author__ = "Devank U"
__email__ = "devank@example.com"

# Make the package contents easily accessible
import os

def get_algorithms_file_path():
    """Returns the path to the l1.py algorithms file"""
    return os.path.join(os.path.dirname(__file__), 'l1.py')

def copy_algorithms_file(destination='.'):
    """
    Copy the l1.py algorithms file to a specified destination
    
    Args:
        destination (str): Directory where the file should be copied (default: current directory)
    
    Returns:
        str: Path to the copied file
    """
    import shutil
    source = get_algorithms_file_path()
    dest_path = os.path.join(destination, 'l1.py')
    shutil.copy(source, dest_path)
    return dest_path

__all__ = ['get_algorithms_file_path', 'copy_algorithms_file']
