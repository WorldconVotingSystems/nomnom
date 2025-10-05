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
