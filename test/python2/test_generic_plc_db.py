import sqlite3

import pytest
from mock import call

from dhalsim.python2.generic_plc import GenericPLC, DatabaseError


@pytest.fixture
def patched_plc(mocker):
    mocker.patch.object(GenericPLC, "__init__", return_value=None)
    mocker.patch.object(GenericPLC, "DB_TRIES", 3)
    cur_mock = mocker.Mock()
    conn_mock = mocker.Mock()
    logger_mock = mocker.Mock()

    plc = GenericPLC()
    plc.cur = cur_mock
    plc.conn = conn_mock
    plc.logger = logger_mock
    plc.intermediate_plc = {
        'name': 'patched_plc'
    }

    return plc, cur_mock, conn_mock, logger_mock


def test_get_master_clock_first_try(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.fetchone.return_value = [5]

    assert plc.get_master_clock() == 5

    cur_mock.execute.assert_called_once_with("SELECT time FROM master_time WHERE id IS 1")
    cur_mock.fetchone.assert_called_once()
    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0


def test_get_master_clock_fail_once(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    cur_mock.fetchone.return_value = [5]

    assert plc.get_master_clock() == 5

    cur_mock.execute.assert_has_calls([call("SELECT time FROM master_time WHERE id IS 1"),
                                       call("SELECT time FROM master_time WHERE id IS 1")])
    assert cur_mock.execute.call_count == 2
    cur_mock.fetchone.assert_called_once()
    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0


def test_get_master_clock_fail_all(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        plc.get_master_clock()

    cur_mock.execute.assert_has_calls([call("SELECT time FROM master_time WHERE id IS 1"),
                                       call("SELECT time FROM master_time WHERE id IS 1"),
                                       call("SELECT time FROM master_time WHERE id IS 1")])
    assert cur_mock.execute.call_count == 3
    cur_mock.fetchone.assert_not_called()
    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1


def test_get_sync_first_try(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.fetchone.return_value = [1]

    assert plc.get_sync() is True

    cur_mock.execute.assert_called_once_with("SELECT flag FROM sync WHERE name IS ?", ('patched_plc',))
    cur_mock.fetchone.assert_called_once()
    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0


def test_get_sync_fail_once(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    cur_mock.fetchone.return_value = [1]

    assert plc.get_sync() is True

    cur_mock.execute.assert_has_calls([call("SELECT flag FROM sync WHERE name IS ?", ('patched_plc',)),
                                       call("SELECT flag FROM sync WHERE name IS ?", ('patched_plc',))])
    assert cur_mock.execute.call_count == 2
    cur_mock.fetchone.assert_called_once()
    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0


def test_get_sync_fail_all(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        plc.get_sync()

    cur_mock.execute.assert_has_calls([call("SELECT flag FROM sync WHERE name IS ?", ('patched_plc',)),
                                       call("SELECT flag FROM sync WHERE name IS ?", ('patched_plc',)),
                                       call("SELECT flag FROM sync WHERE name IS ?", ('patched_plc',))])
    assert cur_mock.execute.call_count == 3
    cur_mock.fetchone.assert_not_called()
    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1


def test_set_sync_first_try(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    plc.set_sync(True)

    cur_mock.execute.assert_called_once_with("UPDATE sync SET flag=? WHERE name IS ?", (1, 'patched_plc',))
    conn_mock.commit.assert_called_once()
    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0


def test_set_sync_fail_once(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    plc.set_sync(True)

    cur_mock.execute.assert_has_calls([call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'patched_plc',)),
                                       call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'patched_plc',))])
    assert cur_mock.execute.call_count == 2
    conn_mock.commit.assert_called_once()
    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0


def test_set_sync_fail_all(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        plc.set_sync(True)

    cur_mock.execute.assert_has_calls([call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'patched_plc',)),
                                       call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'patched_plc',)),
                                       call("UPDATE sync SET flag=? WHERE name IS ?", (1, 'patched_plc',))])
    assert cur_mock.execute.call_count == 3
    conn_mock.commit.assert_not_called()
    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1


def test_set_attack_flag_first_try(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    plc.set_attack_flag(True, 'test_attack')

    cur_mock.execute.assert_called_once_with("UPDATE attack SET flag=? WHERE name IS ?", (1, 'test_attack',))
    conn_mock.commit.assert_called_once()
    assert logger_mock.debug.call_count == 0
    assert logger_mock.error.call_count == 0


def test_set_attack_flag_fail_once(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), None]

    plc.set_attack_flag(True, 'test_attack')

    cur_mock.execute.assert_has_calls([call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'test_attack',)),
                                       call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'test_attack',))])
    assert cur_mock.execute.call_count == 2
    conn_mock.commit.assert_called_once()
    assert logger_mock.debug.call_count == 1
    assert logger_mock.error.call_count == 0


def test_set_attack_flag_fail_all(patched_plc):
    plc, cur_mock, conn_mock, logger_mock = patched_plc

    cur_mock.execute.side_effect = [sqlite3.OperationalError(), sqlite3.OperationalError(),
                                    sqlite3.OperationalError(), None]

    with pytest.raises(DatabaseError):
        plc.set_attack_flag(True, 'test_attack')

    cur_mock.execute.assert_has_calls([call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'test_attack',)),
                                       call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'test_attack',)),
                                       call("UPDATE attack SET flag=? WHERE name IS ?", (1, 'test_attack',))])
    assert cur_mock.execute.call_count == 3
    conn_mock.commit.assert_not_called()
    assert logger_mock.debug.call_count == 3
    assert logger_mock.error.call_count == 1
