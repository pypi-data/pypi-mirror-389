from src.heros.zenoh import session_manager
from src.heros.heros import LocalHERO
import time


def test_create_destroy():
    manager = session_manager
    with LocalHERO("test_hero_with_manager", session_manager=manager) as hero:
        assert manager._referrers == [hero]
    manager.release_session(hero)

    del hero
    time.sleep(0.2)
    assert manager._referrers == []
    manager.force_close()
