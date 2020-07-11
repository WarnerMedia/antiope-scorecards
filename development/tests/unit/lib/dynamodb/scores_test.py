from lib.dynamodb.scores import ScoresTable


class TestScoresHandler:
    def test_weighted_score_aggregate_calc(self):
        """Test to assess the correct aggregate score is returned."""
        test_score_object = [
            {'score': {'critical': {'weight': 5, 'numResources': 5, 'numFailing': 5}}},
            {'score': {'critical': {'weight': 5, 'numResources': 10, 'numFailing': 10}}},
            {'score': {'high': {'weight': 10, 'numResources': 15, 'numFailing': 15}}},
            {'score': {'high': {'weight': 15, 'numResources': 10, 'numFailing': 10}}},
            {
                'score': {
                    'high': {
                        'weight': 15,
                        'numResources': ScoresTable.NOT_APPLICABLE,
                        'numFailing': ScoresTable.NOT_APPLICABLE,
                    }
                }
            },
            {
                'score': {
                    'high': {
                        'weight': 15,
                        'numResources': ScoresTable.DATA_NOT_COLLECTED,
                        'numFailing': ScoresTable.DATA_NOT_COLLECTED,
                    }
                }
            },
        ]

        aggregate_scores = ScoresTable.weighted_score_aggregate_calc(test_score_object)

        expected_results = {
            'critical': {'numFailing': 15, 'numResources': 15, 'weight': 5},
            'high': {'numFailing': 25, 'numResources': 25, 'weight': 15},
        }

        assert aggregate_scores == expected_results
