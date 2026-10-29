"""Manifest JSON must survive filesystem byte paths and retain reader permissions."""
import json
import os
from pathlib import Path
import stat

import pytest

from tools.delegation_live_log import create_live_transcripts, update_manifest_statuses


@pytest.mark.platforms("posix")
def test_manifest_round_trips_a_non_utf8_profile_path(tmp_path):
    home = tmp_path / os.fsdecode(b"profile_\xff")
    ident, _, paths = create_live_transcripts([{"goal": "inspect files"}], home=home)
    path = Path(paths[0]).parent / "manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["tasks"][0]["log"] == paths[0]
    update_manifest_statuses(ident, [{"task_index": 0, "status": "completed"}], home=home)
    assert json.loads(path.read_text(encoding="utf-8"))["tasks"][0]["status"] == "completed"
    assert stat.S_IMODE(path.stat().st_mode) == 0o644


@pytest.mark.platforms("posix")
def test_manifest_updates_preserve_existing_permissions(tmp_path):
    ident, _, paths = create_live_transcripts([{"goal": "检查"}], home=tmp_path)
    path = Path(paths[0]).parent / "manifest.json"
    path.chmod(0o640)
    update_manifest_statuses(ident, [{"task_index": 0, "status": "completed"}], home=tmp_path)
    assert stat.S_IMODE(path.stat().st_mode) == 0o640
    assert json.loads(path.read_text(encoding="utf-8"))["tasks"][0]["goal"] == "检查"
