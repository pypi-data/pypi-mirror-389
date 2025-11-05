import json
import pytest

from src.lunar_policy import Check, Node


class TestCheckGet:
    def test_get_valid_path_workflows_finished(self):
        data = Node.from_merged_json(json.dumps({'hi': 'there'}), bundle_info={'workflows_finished': True})

        with Check('test', data=data) as c:
            c.get_value('.hi')

    def test_get_valid_path_workflows_not_finished(self):
        data = Node.from_merged_json(json.dumps({'hi': 'there'}), bundle_info={'workflows_finished': False})

        with Check('test', data=data) as c:
            c.get_value('.hi')

    def test_get_missing_path_workflows_finished(self):
        data = Node.from_merged_json('{}', bundle_info={'workflows_finished': True})

        with pytest.raises(ValueError):
            with Check('test', data=data) as c:
                c.get_value('.missing')

    def test_get_missing_path_workflows_not_finished(self, capsys):
        data = Node.from_merged_json('{}', bundle_info={'workflows_finished': False})

        with Check('test', data=data) as c:
            c.get_value('.missing')

        captured = capsys.readouterr()
        results = json.loads(captured.out)['assertions']
        assert len(results) == 1
        assert results[0]['result'] == 'no-data'
        assert '.missing' in results[0]['failure_message']
        assert results[0]['op'] == 'fail'

    def test_get_invalid_path(self):
        data = Node.from_merged_json('{}')

        with pytest.raises(ValueError):
            with Check('test', data=data) as c:
                c.get_value('@#$@#$@#$')

    def test_get_all_valid_path_single(self):
        data = Node.from_bundle_json(
            json.dumps(
                {
                    'bundle_info': {},
                    'merged_blob': {},
                    'metadata_instances': [{'payload': {'hi': 'there'}}],
                }
            )
        )

        all = []
        with Check('test', data=data) as c:
            all = c.get_all_values('.hi')

        assert all == ['there']

    def test_get_all_valid_path_multiple(self):
        data = Node.from_bundle_json(
            json.dumps(
                {
                    'bundle_info': {},
                    'merged_blob': {},
                    'metadata_instances': [
                        {'payload': {'hi': 'there'}},
                        {'payload': {'hi': 'there'}},
                    ],
                }
            )
        )

        all = []
        with Check('test', data=data) as c:
            all = c.get_all_values('.hi')

        assert all == ['there', 'there']

    def test_get_all_invalid_path(self):
        data = Node.from_merged_json('{}')

        with pytest.raises(ValueError):
            with Check('test', data=data) as c:
                c.get_all_values('@#$@#$@#$')


class TestCheckIteration:
    def test_iteration(self):
        data = Node.from_merged_json(json.dumps({'hi': 'there'}))

        with Check('test', data=data) as c:
            for key in c:
                assert key == 'hi'

    def test_items(self):
        data = Node.from_merged_json(json.dumps({'hi': 'there'}))

        with Check('test', data=data) as c:
            for key, node in c.items():
                assert key == 'hi'
                assert node.get_value() == 'there'
