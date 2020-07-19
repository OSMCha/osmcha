class Warnings(object):
    def __init__(self):
        self.tags = [
            {'tag': 'warnings:almost_junction', 'reason': 'Almost junction', 'exact_match': False},
            {'tag': 'warnings:close_nodes', 'reason': 'Very close points', 'exact_match': False},
            {'tag': 'warnings:crossing_ways', 'reason': 'Crossing ways', 'exact_match': False},
            {'tag': 'warnings:disconnected_way', 'reason': 'Disconnected way', 'exact_match': False},
            {'tag': 'warnings:impossible_oneway', 'reason': 'Impossible oneway', 'exact_match': False},
            {'tag': 'warnings:incompatible_source', 'reason': 'suspect_word', 'exact_match': False},
            {'tag': 'warnings:mismatched_geometry', 'reason': 'Mismatched geometry', 'exact_match': False},
            {'tag': 'warnings:missing_role', 'reason': 'Missing role', 'exact_match': False},
            {'tag': 'warnings:missing_tag', 'reason': 'Missing tag', 'exact_match': False},
            {'tag': 'warnings:outdated_tags', 'reason': 'Outdated tags', 'exact_match': False},
            {'tag': 'warnings:private_data', 'reason': 'Private information', 'exact_match': False},
            {'tag': 'warnings:suspicious_name:generic_name', 'reason': 'Generic name', 'exact_match': True},
            {'tag': 'warnings:unsquare_way', 'reason': 'Unsquare corners', 'exact_match': False},
            ]

    def get_exact_match_warnings(self):
        return [w for w in self.tags if w['exact_match'] is True]

    def get_non_exact_match_warnings(self):
        return [w for w in self.tags if w['exact_match'] is False]

    def is_enabled(self, tag):
        for warning in self.get_exact_match_warnings():
            if warning['tag'] == tag:
                return warning['reason']
        for warning in self.get_non_exact_match_warnings():
            if tag.startswith(warning['tag']):
                return warning['reason']
