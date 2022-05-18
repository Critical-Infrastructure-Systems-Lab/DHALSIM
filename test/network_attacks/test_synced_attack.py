import sqlite3

import pytest
from mock import call

from dhalsim.network_attacks.synced_attack import SyncedAttack, DatabaseError
from dhalsim.network_attacks.cppo_server_mitm_attack import MitmAttack


@pytest.fixture
def patched_attack(mocker):
    sleeper = mocker.patch("time.sleep", return_value=None)
    mocker.patch.object(SyncedAttack, "__init__", return_value=None)
    mocker.patch.object(MitmAttack, "__init__", return_value=None)
    mocker.patch.object(SyncedAttack, "DB_TRIES", 3)
    mocker.patch.object(SyncedAttack, "DB_SLEEP_TIME", 1.5)

    cur_mock = mocker.Mock()
    conn_mock = mocker.Mock()
    logger_mock = mocker.Mock()

    attacker = MitmAttack()
    attacker.cur = cur_mock
    attacker.conn = conn_mock
    attacker.logger = logger_mock
    attacker.intermediate_attack = {
        'name': 'attack123'
    }

    return attacker, cur_mock, conn_mock, logger_mock, sleeper


def test_get_master_clock_first_try(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.fetchone.return_value = [5]

    assert attack.get_master_clock() == 5

    cur_mock.execute.assert_called_once_with("SELECT time FROM master_time WHERE id IS 1")

    cur_mock.fetchone.assert_called_once()

    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0

    sleeper.assert_not_called()


def test_get_master_clock_fail_once(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    cur_mock.fetchone.return_value = [5]

    assert attack.get_master_clock() == 5

    cur_mock.execute.assert_has_calls([call("SELECT time FROM master_time WHERE id IS 1"),
                                       call("SELECT time FROM master_time WHERE id IS 1")])
    assert cur_mock.execute.call_count == 2

    cur_mock.fetchone.assert_called_once()

    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0

    sleeper.assert_called_once_with(1.5)


def test_get_master_clock_fail_all(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        attack.get_master_clock()

    cur_mock.execute.assert_has_calls([call("SELECT time FROM master_time WHERE id IS 1"),
                                       call("SELECT time FROM master_time WHERE id IS 1"),
                                       call("SELECT time FROM master_time WHERE id IS 1")])
    assert cur_mock.execute.call_count == 3

    cur_mock.fetchone.assert_not_called()

    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1

    sleeper.assert_has_calls([call(1.5), call(1.5), call(1.5)])
    assert sleeper.call_count == 3


def test_get_sync_first_try(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.fetchone.return_value = [1]

    assert attack.get_sync() is True

    cur_mock.execute.assert_called_once_with("SELECT flag FROM sync WHERE name IS ?", ('attack123',))

    cur_mock.fetchone.assert_called_once()

    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0

    sleeper.assert_not_called()


def test_get_sync_fail_once(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    cur_mock.fetchone.return_value = [1]

    assert attack.get_sync() is True

    cur_mock.execute.assert_has_calls([call("SELECT flag FROM sync WHERE name IS ?", ('attack123',)),
                                       call("SELECT flag FROM sync WHERE name IS ?", ('attack123',))])
    assert cur_mock.execute.call_count == 2

    cur_mock.fetchone.assert_called_once()

    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0

    sleeper.assert_called_once_with(1.5)


def test_get_sync_fail_all(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        attack.get_sync()

    cur_mock.execute.assert_has_calls([call("SELECT flag FROM sync WHERE name IS ?", ('attack123',)),
                                       call("SELECT flag FROM sync WHERE name IS ?", ('attack123',)),
                                       call("SELECT flag FROM sync WHERE name IS ?", ('attack123',))])
    assert cur_mock.execute.call_count == 3

    cur_mock.fetchone.assert_not_called()

    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1

    sleeper.assert_has_calls([call(1.5),call(1.5),call(1.5)])
    assert sleeper.call_count == 3


def test_set_sync_first_try(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    attack.set_sync(True)

    cur_mock.execute.assert_called_once_with("UPDATE sync SET flag=? WHERE name IS ?", (1, 'attack123',))

    conn_mock.commit.assert_called_once()

    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0

    sleeper.assert_not_called()


def test_set_sync_fail_once(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    attack.set_sync(True)

    cur_mock.execute.assert_has_calls([call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'attack123',)),
                                       call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'attack123',))])
    assert cur_mock.execute.call_count == 2

    conn_mock.commit.assert_called_once()

    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0

    sleeper.assert_called_once_with(1.5)


def test_set_sync_fail_all(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        attack.set_sync(True)

    cur_mock.execute.assert_has_calls([call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'attack123',)),
                                       call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'attack123',)),
                                       call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'attack123',))])
    assert cur_mock.execute.call_count == 3

    conn_mock.commit.assert_not_called()

    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1

    sleeper.assert_has_calls([call(1.5),call(1.5),call(1.5)])
    assert sleeper.call_count == 3


def test_set_attack_flag_first_try(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    attack.set_attack_flag(True)

    cur_mock.execute.assert_called_once_with("UPDATE attack SET flag=? WHERE name IS ?", (1, 'attack123',))

    conn_mock.commit.assert_called_once()

    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0

    sleeper.assert_not_called()


def test_set_attack_flag_fail_once(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    attack.set_attack_flag(True)

    cur_mock.execute.assert_has_calls([call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'attack123',)),
                                       call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'attack123',))])
    assert cur_mock.execute.call_count == 2

    conn_mock.commit.assert_called_once()

    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0

    sleeper.assert_called_once_with(1.5)


def test_set_attack_flag_fail_all(patched_attack):
    attack, cur_mock, conn_mock, logger_mock, sleeper = patched_attack

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        attack.set_attack_flag(True)

    cur_mock.execute.assert_has_calls([call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'attack123',)),
                                       call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'attack123',)),
                                       call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'attack123',))])
    assert cur_mock.execute.call_count == 3

    conn_mock.commit.assert_not_called()

    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1

    sleeper.assert_has_calls([call(1.5),call(1.5),call(1.5)])
    assert sleeper.call_count == 3
