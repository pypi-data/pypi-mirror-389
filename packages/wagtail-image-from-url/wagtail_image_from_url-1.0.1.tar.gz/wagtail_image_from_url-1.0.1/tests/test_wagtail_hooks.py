import pytest  # noqa F401
from wagtail import hooks


def test_register_admin_urls():
    urls = []
    for fn in hooks.get_hooks("register_admin_urls"):
        urls.extend(fn())
    # URLResolver objects: use .pattern.name
    names = [getattr(u, "name", None) or getattr(getattr(u, "pattern", None), "name", None) for u in urls]
    assert "images_w_url_index" in names
    assert "add_from_url" in names


def test_register_admin_menu_item():
    menu_items = [fn() for fn in hooks.get_hooks("register_admin_menu_item")]
    assert any(item.name == "custom_images" for item in menu_items)
