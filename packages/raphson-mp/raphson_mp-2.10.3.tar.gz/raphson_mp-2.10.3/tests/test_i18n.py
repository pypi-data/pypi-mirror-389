from raphson_mp.server import i18n, vars


def test_format_timedelta():
    vars.LOCALE.set("en")
    assert i18n.format_timedelta(10) == "Just now"
    assert i18n.format_timedelta(67) == "1 minute ago"
    assert i18n.format_timedelta(301) == "5 minutes ago"
    assert i18n.format_timedelta(7201) == "2 hours ago"
    assert i18n.format_timedelta(80000) == "22 hours ago"
    assert i18n.format_timedelta(433405) == "5 days ago"
