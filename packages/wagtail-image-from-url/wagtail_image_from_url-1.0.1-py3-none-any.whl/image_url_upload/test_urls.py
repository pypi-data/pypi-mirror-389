from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from image_url_upload import views

urlpatterns = [
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    # Include your app's custom URLs via hooks
    path("images/add_from_url/", views.AddFromURLView.as_view(), name="add_from_url"),
    path("images-w-url/", views.CustomImageIndexView.as_view(), name="images_w_url_index"),
    # Optionally include the default Wagtail URLs
    path("", include(wagtail_urls)),
]
