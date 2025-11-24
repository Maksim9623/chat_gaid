import zlib
import os
import re


def compress_file(input_file):
    """Сжимаем файл с использованием zlib."""
    if input_file.endswith(('.rar', '.zip', '.7z', '.pdf', '.doc', 'docx')):
            return input_file
    with open(input_file, 'rb') as f:
        data = f.read()
    compressed_data = zlib.compress(data)
    compressed_file = input_file + ".compressed"
    with open(compressed_file, 'wb') as f:
        f.write(compressed_data)
    return compressed_file


def decompress_file(input_file):
    """Распаковка файла с использованием zlib."""
    with open(input_file, 'rb') as f:
        compressed_data = f.read()
    try:
        decompressed_data = zlib.decompress(compressed_data)
        decompressed_file = input_file.replace(".compressed", "")
        with open(decompressed_file, 'wb') as f:
            f.write(decompressed_data)
        return decompressed_file
    except zlib.error as e:
        print(f'Ошибка при распаковки файла {e}')
        return None
   
    
def remove_compressed(file_name):
    if ".compressed" in file_name:
        new_name = file_name.replace(".compressed", "")
        return new_name
    return file_name

