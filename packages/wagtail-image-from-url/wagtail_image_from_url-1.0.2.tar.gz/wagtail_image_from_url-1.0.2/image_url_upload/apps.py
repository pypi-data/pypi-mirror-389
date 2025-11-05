"""
Django app configuration for image_url_upload.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ImageUrlUploadConfig(AppConfig):
    """
    Configuration for the Image URL Upload app.

    This app provides functionality to import images from URLs
    directly into Wagtail's image library.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "image_url_upload"
    label = "image_url_upload"
    verbose_name = _("Image URL Upload")
