import os
import stat
import tempfile
import exiftool
import shutil

class MetadataExtractor:
    def __init__(self):
        self.exif_executable = shutil.which("exiftool")
        if not self.exif_executable:
            self.ptjsonlib.end_error("ExifTool not found. install first and make sure its in PATH.", self.use_json)

    def get_metadata(self, response=None, path_to_local_file=None) -> dict:
        if response is not None:
            tmp = tempfile.NamedTemporaryFile()
            with open(tmp.name, 'wb') as f:
                f.write(response.content)
            with exiftool.ExifTool(executable=self.exif_executable) as exif_tool:
                result_dict = exif_tool.execute_json(tmp.name)[0]

        elif path_to_local_file:
            with exiftool.ExifTool(executable=self.exif_executable) as exif_tool:
                result_dict = exif_tool.execute_json(path_to_local_file)[0]

        blacklisted_keys = ["SourceFile", "ExifTool:ExifToolVersion", "File:FileName", "File:Directory", "File:FileSize", "File:FileModifyDate", "File:FileInodeChangeDate", "File:FilePermissions", "File:FileAccessDate", "File:FileType", "File:FileTypeExtension", "File:MIMEType"]
        result_dict = {k: v for k, v in result_dict.items() if k not in blacklisted_keys and v}

        return result_dict