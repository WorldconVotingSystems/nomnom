from nomnom.convention import ConventionTheme


def test_convention_theme_stylesheet():
    assert ConventionTheme().get_stylesheet(None) == "css/nominate.css"


def test_subclass_convention_theme_stylesheet():
    class MyTheme(ConventionTheme):
        stylesheet = "css/mytheme.css"

    assert MyTheme().get_stylesheet(None) == "css/mytheme.css"
