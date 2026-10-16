import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_ownership as co  # noqa: E402


def test_categories():
    assert co.category("mira_tv/cli.py") == "D"
    assert co.category("tests/test_x.py") == "D"
    assert co.category("app/mira/reportFocus.ts") == "V"
    assert co.category("bugs/BUG-01-x.patch") == "V"
    assert co.category("BUILD.md") == "LOCKED"
    assert co.category("docs/FRICTION_LOG.md") == "SHARED"
    assert co.category("DECISION.md") == "SHARED"
    assert co.category("random/new.txt") == "UNOWNED"


def test_d_cannot_touch_v_files():
    bad = co.violations("D", ["app/x.tsx", "mira_tv/cli.py"])
    assert [f for f, _ in bad] == ["app/x.tsx"]


def test_v_cannot_touch_d_files():
    bad = co.violations("V", ["mira_tv/cli.py", "report/template.html"])
    assert [f for f, _ in bad] == ["mira_tv/cli.py"]


def test_locked_needs_contract_change():
    assert co.violations("D", ["BUILD.md"])
    assert co.violations("D", ["BUILD.md"], contract_change=True) == []


def test_shared_and_unowned():
    assert co.violations("V", ["docs/FRICTION_LOG.md"]) == []
    assert co.violations("D", ["new_folder/x.py"])


def test_windows_paths():
    assert co.category("mira_tv\\cli.py") == "D"


def test_no_pattern_claimed_by_both():
    for pat in co.D_OWNS:
        probe = pat[:-2] + "/x" if pat.endswith("/**") else pat
        assert not co.matches(probe, co.V_OWNS), pat
    for pat in co.V_OWNS:
        probe = pat[:-2] + "/x" if pat.endswith("/**") else pat
        assert not co.matches(probe, co.D_OWNS), pat
