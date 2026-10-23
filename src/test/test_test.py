import os


def test_logfile_is_not_empty():
    path = "~/src/agent/output/" + "log.json"
    logsize = os.path.getsize(path)
    assert logsize != 0