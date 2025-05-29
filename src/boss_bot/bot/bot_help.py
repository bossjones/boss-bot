"""Custom help command implementation."""

from typing import Any

import discord
from discord.ext import commands


class BossHelpCommand(commands.DefaultHelpCommand):
    """Custom help command for Boss-Bot."""

    def __init__(self):
        """Initialize the help command with custom settings."""
        super().__init__(
            no_category="General Commands",
            dm_help=False,
            sort_commands=True,
            case_insensitive=True,
            width=65,
            indent=2,
        )

    def get_command_signature(self, command: commands.Command) -> str:
        """Get the command signature with proper formatting."""
        parent: commands.GroupMixin[Any] | None = command.parent
        entries: list[str] = []
        # command.parent is type-hinted as GroupMixin some attributes are resolved via MRO
        while parent is not None:
            entries.append(parent.name)  # type: ignore
            parent = parent.parent  # type: ignore
        parent_sig = " ".join(reversed(entries))
        alias = command.name if not parent_sig else f"{parent_sig} {command.name}"

        return f"{self.context.clean_prefix}{alias} {command.signature}"

    async def send_bot_help(self, mapping):
        """Send the bot help message with a nice embed."""
        embed = discord.Embed(
            title="Boss-Bot Help",
            description="A Discord bot for downloading and managing media files.",
            color=discord.Color.blue(),
        )

        # Add command list
        for cog, commands_list in mapping.items():
            filtered = await self.filter_commands(commands_list, sort=True)
            if filtered:
                cog_name = getattr(cog, "qualified_name", "General")
                embed.add_field(
                    name=cog_name,
                    value="\n".join(f"`{self.get_command_signature(c)}` - {c.short_doc}" for c in filtered),
                    inline=False,
                )

        # Add footer with additional info
        embed.set_footer(text=f"Type {self.context.clean_prefix}help <command> for more info on a command.")

        # Send the help embed
        destination = self.get_destination()
        await destination.send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        """Send help for a specific command with a nice embed."""
        embed = discord.Embed(
            title=f"Command: {self.get_command_signature(command)}",
            description=command.help or "No description available.",
            color=discord.Color.blue(),
        )

        # Add aliases if they exist
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{alias}`" for alias in command.aliases), inline=False)

        # Add cooldown info if it exists
        if command._buckets and command._buckets._cooldown:
            embed.add_field(
                name="Cooldown",
                value=f"{command._buckets._cooldown.rate} uses per {command._buckets._cooldown.per} seconds",
                inline=False,
            )

        # Send the command help embed
        destination = self.get_destination()
        await destination.send(embed=embed)

    async def send_error_message(self, error: str):
        """Send error message with a nice embed."""
        embed = discord.Embed(title="Help Error", description=error, color=discord.Color.red())

        destination = self.get_destination()
        await destination.send(embed=embed)
