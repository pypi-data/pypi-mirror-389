import pytest


def test_method(local_hero_device, remote_hero_device):
    assert remote_hero_device.my_method("test str") == local_hero_device.my_method("test str")


def test_complex_signature(local_hero_device, remote_hero_device):
    res = remote_hero_device.complex_signature(200, 100, 1, 2, kw2="str", kw3="test", kw=5)
    assert res == [200, 100, [1, 2], 5, {"kw2": "str", "kw3": "test"}]
    res = remote_hero_device.weird_name_signature(200, kwargs="weird")
    assert res == [200, "weird"]


def test_arg(local_hero_device, remote_hero_device):
    assert remote_hero_device.int_var == local_hero_device.int_var
    remote_hero_device.int_var = 10
    assert remote_hero_device.int_var == local_hero_device.int_var


def test_force_remote_local(remote_hero_device, local_hero_device):
    with pytest.raises(AttributeError):
        remote_hero_device.forced_local()
    with pytest.raises(AttributeError):
        remote_hero_device._local_only()
    assert local_hero_device._local_only()
    assert remote_hero_device._forced_remote()


def test_arg_from_annotation(remote_hero_device, local_hero_device):
    caps = remote_hero_device._get_capabilities()
    assert any(getattr(cap, "name", None) == "annotated_arg" for cap in caps)
    assert any(getattr(cap, "name", None) == "some_object" for cap in caps)
    remote_hero_device.annotated_arg = "test"
    assert local_hero_device.annotated_arg == "test"


def test_annotated_callable(remote_hero_device, local_hero_device):
    assert any(getattr(cap, "name", None) == "annotated_method" for cap in local_hero_device.capabilities)
    assert local_hero_device.annotated_method == local_hero_device.my_method
    # Currently methods are not seriazable so this fails (see https://gitlab.com/atomiq-project/heros/-/issues/25)
    # assert remote_hero_device.annotated_method("test") == "test"
