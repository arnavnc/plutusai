import discord
from discord.ext import commands
from ..config import settings
from ..services.openai_service import openai_service
from ..services.openalex import openalex_service
import asyncio
from typing import Optional, Callable
import logging
import sys
import json
from textwrap import wrap

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        # Set up intents with all the permissions we need
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        # Permission integer: READ_MESSAGES (1 << 10) | SEND_MESSAGES (1 << 11) | 
        # READ_MESSAGE_HISTORY (1 << 16) | USE_APPLICATION_COMMANDS (1 << 31)
        permissions = 274878221312

        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=settings.discord_client_id
        )
        self.message_callback: Optional[Callable[[str], None]] = None

    async def setup_hook(self):
        logger.info("Bot is setting up...")
        
        # Remove default help command before adding our custom one
        self.remove_command('help')

        # Add commands
        @self.command(name="hello")
        async def hello(ctx):
            """Say hello to the bot"""
            await ctx.send(f"Hello {ctx.author.name}! 👋")

        @self.command(name="search")
        async def search(ctx, *, description: str):
            """Search for funding opportunities with a project description"""
            try:
                # Send initial message
                await ctx.send(f"🔍 Searching for funding opportunities related to: {description}")

                # Generate search terms
                await ctx.send("⚙️ Generating search terms...")
                search_terms = await openai_service.extract_search_terms(description)
                search_terms = search_terms[:3]
                terms_msg = "🎯 Search terms generated:\n" + "\n".join([f"- {term}" for term in search_terms])
                await ctx.send(terms_msg)

                # Search for papers
                papers_found = 0
                funders_data = []
                for term in search_terms:
                    await ctx.send(f"📚 Searching papers for: {term}")
                    term_papers = await openalex_service.search_for_grants([term], 15)
                    funders_data.extend(term_papers)
                    papers_found += len(term_papers)
                    await ctx.send(f"Found {len(term_papers)} papers for '{term}'")

                # Compile funding data
                await ctx.send("🔄 Compiling funding data...")
                enriched_data = await openalex_service.enrich_funders_data(funders_data)

                # Generate summary
                await ctx.send("📝 Generating summary...")
                summary = await openai_service.generate_summary(description, enriched_data)

                # Split and send summary in chunks
                await ctx.send("✨ **Funding Opportunities Report** ✨\n━━━━━━━━━━━━━━━━━━━━━━━")
                # Split summary into chunks of 1900 characters (leaving room for formatting)
                summary_chunks = wrap(summary, 1900)
                for chunk in summary_chunks:
                    await ctx.send(chunk)

                # Send detailed funders data
                if enriched_data:
                    funders_msg = "\n📊 **Top Funding Sources**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
                    for funder in enriched_data[:5]:  # Show top 5 funders
                        funder_name = funder.get('name', 'Unknown Funder')
                        # Skip if funder name is unknown or N/A
                        if funder_name in ['Unknown Funder', 'N/A']:
                            continue
                        grant_count = funder.get('grant_count', 'N/A')
                        funders_msg += f"🏛️ **{funder_name}**\n"
                        funders_msg += f"   └ {grant_count} grants funded\n"

                    # Only send if we have valid funders
                    if "🏛️" in funders_msg:
                        await ctx.send(funders_msg)
                    else:
                        await ctx.send("ℹ️ No specific funding sources were identified in the search results.")

                    # # Add recommendations footer
                    # await ctx.send("\n💡 **Next Steps**\n━━━━━━━━━━━━━━━━━━━━━━━\n" +
                    #              "1️⃣ Review the funding opportunities above\n" +
                    #              "2️⃣ Visit the funders' websites for detailed guidelines\n" +
                    #              "3️⃣ Consider reaching out to program officers\n" +
                    #              "4️⃣ Start preparing your grant application materials")

            except Exception as e:
                logger.error(f"Error in search command: {e}")
                await ctx.send(f"❌ An error occurred while searching: {str(e)}")

        @self.command(name="help")
        async def custom_help(ctx):
            """Show available commands"""
            commands_list = [
                "**Available Commands:**",
                "`!hello` - Say hello to the bot",
                "`!search <description>` - Search for funding opportunities",
                "`!help` - Show this help message"
            ]
            await ctx.send("\n".join(commands_list))

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Game(name="!help for commands"))
        
        # Generate invite link with correct permissions
        invite_link = discord.utils.oauth_url(
            settings.discord_client_id,  # Use client_id instead of bot user id
            permissions=discord.Permissions(permissions=274878221312),
            scopes=["bot", "applications.commands"]
        )
        logger.info(f"Invite link: {invite_link}")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        # Process commands if message starts with command prefix
        await self.process_commands(message)

        # If message is in the configured channel, process it
        if str(message.channel.id) == settings.discord_channel_id:
            if self.message_callback:
                await self.message_callback(message.content)

class DiscordService:
    def __init__(self):
        self.bot = DiscordBot()
        self._task: Optional[asyncio.Task] = None

    async def start_bot(self):
        """Start the Discord bot"""
        try:
            self._task = asyncio.create_task(
                self.bot.start(settings.discord_bot_token)
            )
            logger.info("Discord bot started")
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            raise

    async def stop_bot(self):
        """Stop the Discord bot"""
        if self.bot:
            await self.bot.close()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Discord bot stopped")

    async def send_message(self, message: str):
        """Send a message to the configured Discord channel"""
        try:
            channel = self.bot.get_channel(int(settings.discord_channel_id))
            if channel:
                await channel.send(message)
            else:
                logger.error("Could not find configured Discord channel")
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")

    def set_message_callback(self, callback: Callable[[str], None]):
        """Set a callback function to handle incoming messages"""
        self.bot.message_callback = callback

# Create a singleton instance
discord_service = DiscordService() 