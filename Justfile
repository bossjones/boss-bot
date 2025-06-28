# https://just.systems/man/en/

# Import common configuration and variables
import "justfiles/common.just"
import "justfiles/variables.just"

# Import task groups
import "justfiles/cz.just"
import "justfiles/check.just"
import "justfiles/clean.just"
import "justfiles/format.just"
import "justfiles/package.just"
import "justfiles/install.just"
import "justfiles/doc.just"
import "justfiles/release.just"
import "justfiles/uv.just"
import "justfiles/changelog.just"
import "justfiles/towncrier.just"
import "justfiles/validate.just"
import "justfiles/security.just"
import "justfiles/convert.just"
import "justfiles/taplo.just"
import "justfiles/firecrawl.just"
import "justfiles/audit.just"
import "justfiles/test.just"
import "justfiles/smoke-test.just"
import "justfiles/langgraph-cli.just"
import "justfiles/langgraph-gen.just"
import "justfiles/mcp.just"
import "justfiles/datasette.just"
import "justfiles/dev.just"
# display help information
default:
	@just --list
