from src.lunar_policy import Check, CheckStatus, Node


class TestCheckName:
    def test_name(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            c.assert_true(True)

        assert c.name == 'test'


class TestCheckFailureReasons:
    def test_failure_reasons_single(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            c.fail('this failed')

        assert c.failure_reasons == ['this failed']

    def test_failure_reasons_multiple(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            c.fail('this failed')
            c.fail('this failed too')

        assert c.failure_reasons == ['this failed', 'this failed too']


class TestCheckStatus:
    def test_status_pass(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            c.assert_true(True)

        assert c.status == CheckStatus.PASS

    def test_status_fail(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            c.fail('this failed')

        assert c.status == CheckStatus.FAIL

    def test_status_no_data(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            c.get_value('.not.a.path')

        assert c.status == CheckStatus.NO_DATA

    def test_status_no_assertions(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            pass

        assert c.status == CheckStatus.PASS

    def test_fail_before_pass(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            c.assert_true(True)
            c.fail('this failed')

        assert c.status == CheckStatus.FAIL

    def test_no_data_before_pass(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            c.assert_true(True)
            c.get_value('.not.a.path')

        assert c.status == CheckStatus.NO_DATA

    def test_no_data_before_fail(self):
        data = Node.from_merged_json('{}')

        with Check('test', data=data) as c:
            c.fail('this failed')
            c.get_value('.not.a.path')

        assert c.status == CheckStatus.NO_DATA
