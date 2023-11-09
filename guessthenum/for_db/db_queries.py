check_user_query: str = """
SELECT *
FROM `users_info`
WHERE %s = `user_id`
"""


add_user_query: str = """
INSERT INTO `users_info` (`user_id`, `username`, `total_games`, `wins`, `game_score`)
VALUES (%s, '%s', %s, %s, %s)
"""


update_user_info_query: str = """
UPDATE `users_info`
SET `total_games` = `total_games` + 1, `wins` = `wins` + %s, `game_score` = `game_score` + %s
WHERE `user_id` > 0 AND %s = `user_id`
"""


select_user_info_query: str = """
SELECT `total_games`, `wins`, `game_score`
FROM `users_info`
WHERE %s = `user_id`
"""