# install datasette plugins
[group('datasette')]
install-plugins:
	uv run datasette install dclient
# install datasette plugins
[group('datasette')]
install-browser:
	uv run shot-scraper install
