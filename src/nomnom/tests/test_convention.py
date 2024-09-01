from nomnom.convention import ConventionTheme


def test_convention_theme_stylesheet_contains_the_main_stylesheet():
    assert "css/nominate.css" in ConventionTheme(
        stylesheets="css/nominate.css", font_urls="fonts"
    ).get_stylesheets(None)


def test_convention_theme_stylesheet_is_a_list():
    assert isinstance(
        ConventionTheme(
            stylesheets="css/nominate.css", font_urls="fonts"
        ).get_stylesheets(None),
        list,
    )


def test_convention_theme_font_url_contains_the_font_url():
    assert "fonts" in ConventionTheme(
        stylesheets="css/nominate.css", font_urls="fonts"
    ).get_font_urls(None)


def test_convention_theme_font_url_is_a_list():
    assert isinstance(
        ConventionTheme(
            stylesheets="css/nominate.css", font_urls="fonts"
        ).get_font_urls(None),
        list,
    )


def test_convention_theme_stylesheet_settings_is_a_list():
    assert {
        "url": "css/nominate.css",
        "rel": "stylesheet",
        "static": True,
    } in ConventionTheme(
        stylesheets="css/nominate.css", font_urls="fonts"
    ).get_stylesheet_settings(None)


def test_convention_theme_stylesheet_settings_when_remote():
    assert {
        "url": "http://css/nominate.css",
        "rel": "stylesheet",
        "static": False,
    } in ConventionTheme(
        stylesheets="http://css/nominate.css", font_urls="fonts"
    ).get_stylesheet_settings(None)


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
