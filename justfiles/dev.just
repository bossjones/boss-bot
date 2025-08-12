# Display a treemap of the timings reported by python -X importtime
[group('dev')]
importtime:
	uv run python -X importtime -m boss_bot.cli.main:entry
