import datetime

from gameset.scores import Leaderboard


def test_leaderboard_ranks_and_persists(tmp_path):
    path = tmp_path / 'scores.json'
    board = Leaderboard(path)
    assert board.add('classic', 50, 5, 120) == 1
    assert board.add('classic', 80, 8, 200) == 1
    assert board.add('classic', 50, 5, 100) == 2  # same score, faster time beats the 120s game
    reloaded = Leaderboard(path)
    assert [e.score for e in reloaded.top('classic')] == [80, 50, 50]
    assert reloaded.top('timed') == []


def test_daily_leaderboard_is_per_day(tmp_path):
    board = Leaderboard(tmp_path / 's.json')
    board.add('daily', 10, 1, 60, day=datetime.date(2026, 1, 1))
    assert board.add('daily', 5, 1, 60, day=datetime.date(2026, 1, 2)) == 1
    assert len(board.top('daily', day='2026-01-02')) == 1


def test_corrupt_file_is_ignored(tmp_path):
    path = tmp_path / 'scores.json'
    path.write_text('not json')
    assert Leaderboard(path).entries == []


def test_low_scores_fall_off(tmp_path):
    board = Leaderboard(tmp_path / 's.json')
    for score in range(10, 20):
        board.add('timed', score, 1, 180)
    assert board.add('timed', 0, 0, 180) is None
