"""
Wagtail Image From URL - A plugin to import images from URLs into Wagtail CMS.

This package provides functionality to add images to Wagtail's image library
directly from URLs without manual download.
"""

__version__ = "0.1.0"
__author__ = "Awais Qureshi"
__license__ = "MIT"
__all__ = ["ImageUrlUploadConfig"]

default_app_config = "image_url_upload.apps.ImageUrlUploadConfig"
