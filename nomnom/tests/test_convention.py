from nomnom.convention import ConventionTheme


def test_convention_theme_stylesheet_is_a_list():
    assert ConventionTheme(
        stylesheets="css/nominate.css", font_urls="fonts"
    ).get_stylesheets(None) == ["css/nominate.css"]


def test_convention_theme_font_url_is_a_list():
    assert ConventionTheme(
        stylesheets="css/nominate.css", font_urls="fonts"
    ).get_font_urls(None) == ["fonts"]


def test_convention_theme_stylesheet_settings_is_a_list():
    assert ConventionTheme(
        stylesheets="css/nominate.css", font_urls="fonts"
    ).get_stylesheet_settings(None) == [
        {"url": "css/nominate.css", "rel": "stylesheet", "static": True}
    ]


def test_convention_theme_stylesheet_settings_when_remote():
    assert ConventionTheme(
        stylesheets="http://css/nominate.css", font_urls="fonts"
    ).get_stylesheet_settings(None) == [
        {"url": "http://css/nominate.css", "rel": "stylesheet", "static": False}
    ]


def test_convention_theme_font_url_settings_is_a_list():
    assert ConventionTheme(
        stylesheets="css/nominate.css", font_urls="fonts"
    ).get_font_url_settings(None) == [
        {"url": "fonts", "rel": "stylesheet", "static": True}
    ]


def test_convention_theme_font_url_settings_when_remote():
    assert ConventionTheme(
        stylesheets="css/nominate.css", font_urls="http://fonts"
    ).get_font_url_settings(None) == [
        {"url": "http://fonts", "rel": "stylesheet", "static": False}
    ]
