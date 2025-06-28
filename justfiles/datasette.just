# install datasette plugins
[group('datasette')]
install-plugins:
	uv run datasette install dclient
# install datasette plugins
[group('datasette')]
install-browser:
	uv run shot-scraper install

# run datasette with configured databases and metadata
[group('datasette')]
datasette-setup:
	uv run datasette dbs/boss_bot.db dbs/analytics.db --metadata metadata.json -o

# run and open dataset
[group('datasette')]
datasette-run:
	uv run datasette dbs/boss_bot.db dbs/analytics.db -o


# run datasette with configured databases and metadata
[group('datasette')]
datasette-serve:
	uv run datasette serve dbs/boss_bot.db dbs/analytics.db --metadata metadata.json --create --open
