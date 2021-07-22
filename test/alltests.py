import unittest

from opensipscli.db import make_url

class OpenSIPSCLIUnitTests(unittest.TestCase):
    def testMakeURL(self):
        u = make_url('x://')
        assert repr(u) == 'x://'
        assert u.drivername == 'x'
        assert all(a is None for a in
            (u.username, u.password, u.host, u.port, u.database))

        u.database = 'db'
        assert repr(u) == str(u) == 'x:///db'

        u.port = 12
        assert repr(u) == str(u) == 'x://:12/db'

        u.host = 'host'
        assert repr(u) == str(u) == 'x://host:12/db'

        u.password = 'pass'
        assert repr(u) == str(u) == 'x://host:12/db'

        u.username = 'user'
        assert repr(u) == 'x://user:***@host:12/db'
        assert str(u) == 'x://user:pass@host:12/db'

        u = make_url('mysql://opensips:opensipsrw@localhost/opensips')
        assert repr(u) == 'mysql://opensips:***@localhost/opensips'
        assert str(u) == 'mysql://opensips:opensipsrw@localhost/opensips'

        u = make_url('mysql://opensips:opensipsrw@localhost')
        assert repr(u) == 'mysql://opensips:***@localhost'
        assert str(u) == 'mysql://opensips:opensipsrw@localhost'

        u = make_url('mysql://root@localhost')
        assert repr(u) == 'mysql://root@localhost'
        assert str(u) == 'mysql://root@localhost'


if __name__ == "__main__":
    unittest.main()
