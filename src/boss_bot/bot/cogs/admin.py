"""Discord cog for admin and help commands."""

import discord
from discord.ext import commands

from boss_bot.bot.client import BossBot


class AdminCog(commands.Cog):
    """Cog for admin and general bot information commands."""

    def __init__(self, bot: BossBot):
        """Initialize the cog."""
        self.bot = bot

    @commands.command(name="info")
    async def show_info(self, ctx: commands.Context):
        """Display bot information including prefix and available commands."""
        embed = discord.Embed(
            title="🤖 Boss-Bot Information",
            description="A Discord Media Download Assistant",
            color=discord.Color.blue(),
        )

        # Bot basic info
        embed.add_field(
            name="📋 Bot Details",
            value=f"**Version:** {self.bot.version}\n"
            f"**Prefix:** `{self.bot.command_prefix}`\n"
            f"**Servers:** {len(self.bot.guilds)}\n"
            f"**Users:** {len(self.bot.users)}",
            inline=True,
        )

        # Supported platforms
        embed.add_field(
            name="🌐 Supported Platforms",
            value="• Twitter/X 🐦\n• Reddit 🤖\n• Instagram 📷\n• YouTube 📺\n• And more!",
            inline=True,
        )

        # Quick help
        embed.add_field(
            name="❓ Need Help?",
            value=f"Use `{self.bot.command_prefix}help` for all commands\n"
            f"Use `{self.bot.command_prefix}commands` for command list\n"
            f"Use `{self.bot.command_prefix}prefixes` for prefix info",
            inline=False,
        )

        embed.set_footer(text="Boss-Bot | Made with discord.py")
        await ctx.send(embed=embed)

    @commands.command(name="prefixes")
    async def show_prefixes(self, ctx: commands.Context):
        """Show supported command prefixes."""
        embed = discord.Embed(
            title="🔧 Command Prefixes",
            description="Here are the supported command prefixes:",
            color=discord.Color.green(),
        )

        embed.add_field(
            name="Current Prefix",
            value=f"`{self.bot.command_prefix}`",
            inline=False,
        )

        embed.add_field(
            name="Usage Examples",
            value=f"`{self.bot.command_prefix}download <url>`\n"
            f"`{self.bot.command_prefix}queue`\n"
            f"`{self.bot.command_prefix}help`",
            inline=False,
        )

        embed.add_field(
            name="📝 Note",
            value="The prefix is configured by the bot administrator and applies to all commands.",
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(name="commands")
    async def list_commands(self, ctx: commands.Context):
        """List all available commands organized by category."""
        embed = discord.Embed(
            title="📚 Available Commands",
            description=f"All commands use the prefix: `{self.bot.command_prefix}`",
            color=discord.Color.purple(),
        )

        # Download commands
        download_commands = [
            f"`{self.bot.command_prefix}download <url>` - Download media from supported platforms",
            f"`{self.bot.command_prefix}metadata <url>` - Get metadata about a URL without downloading",
            f"`{self.bot.command_prefix}status` - Show current download status",
            f"`{self.bot.command_prefix}strategies` - Show download strategy configuration",
            f"`{self.bot.command_prefix}validate-config [platform]` - Validate platform configuration",
            f"`{self.bot.command_prefix}config-summary [platform]` - Show platform config summary",
        ]

        embed.add_field(
            name="📥 Download Commands",
            value="\n".join(download_commands),
            inline=False,
        )

        # Queue commands
        queue_commands = [
            f"`{self.bot.command_prefix}queue [page]` - Show download queue",
            f"`{self.bot.command_prefix}clear` - Clear the download queue",
            f"`{self.bot.command_prefix}remove <id>` - Remove item from queue",
            f"`{self.bot.command_prefix}pause` - Pause download processing",
            f"`{self.bot.command_prefix}resume` - Resume download processing",
        ]

        embed.add_field(
            name="📋 Queue Commands",
            value="\n".join(queue_commands),
            inline=False,
        )

        # Admin/Help commands
        admin_commands = [
            f"`{self.bot.command_prefix}info` - Show bot information",
            f"`{self.bot.command_prefix}prefixes` - Show command prefixes",
            f"`{self.bot.command_prefix}commands` - Show this command list",
            f"`{self.bot.command_prefix}help [command]` - Get detailed help",
        ]

        embed.add_field(
            name="ℹ️ Information Commands",
            value="\n".join(admin_commands),
            inline=False,
        )

        embed.set_footer(text="Use `help <command>` for detailed information about a specific command")
        await ctx.send(embed=embed)

    @commands.command(name="help-detailed")
    async def detailed_help(self, ctx: commands.Context, command_name: str = None):
        """Provide detailed help for a specific command or general usage."""
        if not command_name:
            # General help overview
            embed = discord.Embed(
                title="🆘 Boss-Bot Help",
                description="Welcome to Boss-Bot! Here's how to get started:",
                color=discord.Color.gold(),
            )

            embed.add_field(
                name="🚀 Quick Start",
                value=f"1. Copy any supported URL\n"
                f"2. Use `{self.bot.command_prefix}download <url>`\n"
                f"3. Wait for your download to complete!",
                inline=False,
            )

            embed.add_field(
                name="💡 Pro Tips",
                value=f"• Use `{self.bot.command_prefix}metadata <url>` to preview content before downloading\n"
                f"• Check `{self.bot.command_prefix}queue` to see pending downloads\n"
                f"• Use `{self.bot.command_prefix}strategies` to see platform configurations",
                inline=False,
            )

            embed.add_field(
                name="🔍 Need More Help?",
                value=f"• `{self.bot.command_prefix}commands` - See all available commands\n"
                f"• `{self.bot.command_prefix}help-detailed <command>` - Get help for a specific command\n"
                f"• `{self.bot.command_prefix}prefixes` - See command prefix information",
                inline=False,
            )

            await ctx.send(embed=embed)
            return

        # Help for specific command
        command = self.bot.get_command(command_name)
        if not command:
            await ctx.send(
                f"❌ Command `{command_name}` not found. Use `{self.bot.command_prefix}commands` to see all available commands."
            )
            return

        embed = discord.Embed(
            title=f"📖 Help: {command.name}",
            description=command.help or "No description available.",
            color=discord.Color.blue(),
        )

        # Command signature
        embed.add_field(
            name="📝 Usage",
            value=f"`{self.bot.command_prefix}{command.qualified_name} {command.signature}`",
            inline=False,
        )

        # Command aliases if any
        if command.aliases:
            embed.add_field(
                name="🔄 Aliases",
                value=", ".join(f"`{alias}`" for alias in command.aliases),
                inline=False,
            )

        # Add examples for common commands
        examples = self._get_command_examples(command.name)
        if examples:
            embed.add_field(
                name="💡 Examples",
                value=examples,
                inline=False,
            )

        await ctx.send(embed=embed)

    def _get_command_examples(self, command_name: str) -> str | None:
        """Get usage examples for specific commands."""
        examples = {
            "download": f"`{self.bot.command_prefix}download https://twitter.com/user/status/123`\n"
            f"`{self.bot.command_prefix}download https://reddit.com/r/pics/comments/abc/`\n"
            f"`{self.bot.command_prefix}download https://youtube.com/watch?v=VIDEO_ID`",
            "metadata": f"`{self.bot.command_prefix}metadata https://twitter.com/user/status/123`\n"
            f"`{self.bot.command_prefix}metadata https://instagram.com/p/POST_ID/`",
            "queue": f"`{self.bot.command_prefix}queue`\n`{self.bot.command_prefix}queue 2`",
            "remove": f"`{self.bot.command_prefix}remove download123`",
            "validate-config": f"`{self.bot.command_prefix}validate-config`\n"
            f"`{self.bot.command_prefix}validate-config instagram`",
            "config-summary": f"`{self.bot.command_prefix}config-summary`\n"
            f"`{self.bot.command_prefix}config-summary instagram`",
        }
        return examples.get(command_name)

    # Event Handlers
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is ready."""
        print(f"{type(self).__name__} Cog ready.")

    # Command Error Handlers
    @show_info.error
    async def info_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the info command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in info command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while getting bot information.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @show_prefixes.error
    async def prefixes_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the prefixes command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in prefixes command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while showing prefix information.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @list_commands.error
    async def commands_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the commands command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in commands command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while listing commands.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)

    @detailed_help.error
    async def help_detailed_error_handler(self, ctx: commands.Context, error: commands.CommandError):
        """Handle errors for the help-detailed command."""
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"Command is on cooldown. Try again in {error.retry_after:.1f} seconds.",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            print(f"Unexpected error in help-detailed command: {error}")
            embed = discord.Embed(
                description="An unexpected error occurred while getting detailed help.",
                color=discord.Color.red(),
            )
            await ctx.send(embed=embed)


async def setup(bot: BossBot):
    """Load the AdminCog.

    Args:
        bot: The bot instance
    """
    await bot.add_cog(AdminCog(bot))
