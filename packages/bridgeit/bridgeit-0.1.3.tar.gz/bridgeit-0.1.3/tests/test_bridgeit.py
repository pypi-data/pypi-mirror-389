from bridgeit import installers


def test_pixi_env_sets_crashpad_defaults(monkeypatch) -> None:
    monkeypatch.delenv("MODULAR_SKIP_CRASHPAD", raising=False)
    monkeypatch.delenv("MODULAR_CRASHPAD_DISABLE", raising=False)

    env = installers._pixi_env()

    assert env["MODULAR_SKIP_CRASHPAD"] == "1"
    assert env["MODULAR_CRASHPAD_DISABLE"] == "1"
