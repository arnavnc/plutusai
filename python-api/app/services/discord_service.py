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
        # Store search context for each channel
        self.search_contexts = {}
        # Store conversation history for each channel
        self.conversation_history = {}
        # Store paper details for quick reference
        self.paper_details = {}
        # Store last active timestamp for each channel
        self.last_active = {}

    async def setup_hook(self):
        logger.info("Bot is setting up...")
        
        # Remove default help command before adding our custom one
        self.remove_command('help')

        # Add commands
        @self.command(name="hello")
        async def hello(ctx):
            """Say hello to the bot"""
            await ctx.send(f"👋 Hello {ctx.author.name}! I'm a research funding expert. Use `!help` to see what I can do!")

        @self.command(name="ask")
        async def ask(ctx, *, question: str = None):
            """Ask a follow-up question about the previous search results or specific papers"""
            if question is None:
                await ctx.send("❌ Please provide a question. Example: `!ask What are the typical grant sizes for NIH funding?` or `!ask Tell me more about the paper on RNA sequencing`")
                return

            channel_id = str(ctx.channel.id)
            if channel_id not in self.search_contexts:
                await ctx.send("❌ Please run a search first using `!search` before asking questions.")
                return

            try:
                context = self.search_contexts[channel_id]
                
                # Initialize conversation history if it doesn't exist
                if channel_id not in self.conversation_history:
                    self.conversation_history[channel_id] = []
                
                # Check if this is a new conversation (more than 30 minutes since last message)
                current_time = asyncio.get_event_loop().time()
                if channel_id in self.last_active and current_time - self.last_active[channel_id] > 1800:  # 30 minutes
                    self.conversation_history[channel_id] = []  # Start fresh conversation
                
                # Update last active timestamp
                self.last_active[channel_id] = current_time
                
                # Add the current question to conversation history
                self.conversation_history[channel_id].append({
                    "role": "user",
                    "content": question
                })

                await ctx.send("🤔 Analyzing your question...")
                
                # Get answer from OpenAI
                answer = await openai_service.answer_question(
                    question=question,
                    search_description=context["description"],
                    funders_data=context["funders_data"],
                    enriched_data=context["enriched_data"],
                    conversation_history=self.conversation_history[channel_id],
                    paper_details=self.paper_details.get(channel_id, {})
                )
                
                # Add the answer to conversation history
                self.conversation_history[channel_id].append({
                    "role": "assistant",
                    "content": answer
                })
                
                # Keep conversation history to last 10 exchanges (20 messages)
                if len(self.conversation_history[channel_id]) > 20:
                    self.conversation_history[channel_id] = self.conversation_history[channel_id][-20:]

                # Send the answer with improved formatting
                await ctx.send("━━━━━━━━━━━━━━━━━━━━━━━\n🔍 **Analysis Results** ✨\n━━━━━━━━━━━━━━━━━━━━━━━")
                
                # Process and send each section of the answer
                sections = answer.split('\n\n')  # Split by double newlines to identify sections
                current_section = []
                
                for section in sections:
                    if not section.strip():
                        continue
                        
                    # Check if this is a section header (starts with ###)
                    if section.strip().startswith('###'):
                        # Send previous section if it exists
                        if current_section:
                            await ctx.send('\n'.join(current_section))
                            await asyncio.sleep(0.5)
                            current_section = []
                        
                        # Format the header
                        header = section.strip().replace('###', '').strip()
                        current_section = [f"\n**{header}**"]
                    else:
                        # Format bullet points and regular text
                        lines = section.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('-'):
                                # Split on first colon and format
                                parts = line.strip('- ').split(':', 1)
                                if len(parts) > 1:
                                    current_section.append(f"• **{parts[0].strip()}**: {parts[1].strip()}")
                                else:
                                    current_section.append(f"• {line.strip('- ')}")
                            else:
                                current_section.append(line)
                
                # Send any remaining section
                if current_section:
                    await ctx.send('\n'.join(current_section))

            except Exception as e:
                logger.error(f"Error in ask command: {e}")
                await ctx.send(f"❌ An error occurred while processing your question: {str(e)}")

        @self.command(name="search")
        async def search(ctx, *, description: str = None):
            """Search for funding opportunities with a project description"""
            if description is None:
                await ctx.send("❌ Please provide a project description. Example: `!search research on RNA sequencing`")
                return
            
            try:
                # Store channel ID for context
                channel_id = str(ctx.channel.id)
                
                # Send initial message
                await ctx.send(f"🔍 Searching for funding opportunities related to: {description}")

                # Generate search terms
                await ctx.send("⚙️ Generating search terms...")
                search_terms = await openai_service.extract_search_terms(description)
                search_terms = search_terms[:3]
                terms_msg = "🎯 **Search Terms**\n" + "\n".join([f"• {term}" for term in search_terms])
                await ctx.send(terms_msg)

                # Search for papers
                papers_found = 0
                funders_data = []
                for term in search_terms:
                    await ctx.send(f"📚 Searching papers for: {term}")
                    term_papers = await openalex_service.search_for_grants([term], 5)
                    funders_data.extend(term_papers)
                    papers_found += len(term_papers)
                    await ctx.send(f"Found {len(term_papers)} papers for '{term}'")

                # Compile funding data
                await ctx.send("🔄 Compiling funding data...")
                enriched_data = await openalex_service.enrich_funders_data(funders_data)

                # Store the context for this channel
                self.search_contexts[channel_id] = {
                    "description": description,
                    "search_terms": search_terms,
                    "funders_data": funders_data,
                    "enriched_data": enriched_data
                }

                # Generate summary
                await ctx.send("📝 Generating summary...")
                summary = await openai_service.generate_summary(description, enriched_data)

                # First display search terms
                await ctx.send("━━━━━━━━━━━━━━━━━━━━━━━\n🔍 **Search Terms** ✨\n━━━━━━━━━━━━━━━━━━━━━━━")
                terms_list = "\n".join([f"• {term}" for term in search_terms])
                await ctx.send(terms_list)
                await ctx.send("\n💡 You can ask follow-up questions about these results using the `!ask` command!")
                await asyncio.sleep(0.5)

                # Send Strategic Recommendations
                await ctx.send("\n━━━━━━━━━━━━━━━━━━━━━━━\n✨ **Strategic Recommendations** ✨\n━━━━━━━━━━━━━━━━━━━━━━━")
                
                # Process and send each section of the summary
                lines = summary.split('\n')
                current_section = []
                section_content = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Check if this is a section header
                    if line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.'):
                        # Send previous section if it exists
                        if section_content:
                            await ctx.send('\n'.join(section_content))
                            section_content = []
                            await asyncio.sleep(0.5)
                        
                        # Start new section
                        section_content = [f"**{line.split('.', 1)[1].strip()}**"]
                    else:
                        # Format bullet points
                        if line.startswith('-'):
                            # Split on first colon and format
                            parts = line.strip('- ').split(':', 1)
                            if len(parts) > 1:
                                section_content.append(f"• **{parts[0].strip()}**: {parts[1].strip()}")
                            else:
                                section_content.append(f"• {line.strip('- ')}")
                        else:
                            section_content.append(line)
                
                # Send any remaining section content
                if section_content:
                    await ctx.send('\n'.join(section_content))
                    await asyncio.sleep(0.5)

                # Send funding sources section
                if enriched_data:
                    await ctx.send("\n━━━━━━━━━━━━━━━━━━━━━━━\n📊 **Recent Funding Examples** ✨\n━━━━━━━━━━━━━━━━━━━━━━━\n")
                    
                    # Track unique papers and their funders
                    papers_data = {}  # title -> {paper_info, funders: []}
                    
                    # First pass: Group papers and their funders
                    for item in enriched_data:
                        title = item.get('title', '')
                        if title in papers_data:
                            continue
                            
                        paper_info = {
                            'title': title,
                            'year': item.get('publication_year', ''),
                            'citations': item.get('cited_by_count', 0),
                            'doi': item.get('doi', ''),
                            'id': item.get('id', ''),
                            'funders': []
                        }
                        
                        # Collect all funders for this paper
                        for grant in item.get('grants', []):
                            funder_name = grant.get('funder_display_name', '')
                            if funder_name and funder_name not in ['Unknown Funder', 'N/A']:
                                grant_id = grant.get('award_id', '')
                                funder_info = {
                                    'name': funder_name,
                                    'grant_id': grant_id
                                }
                                if funder_info not in paper_info['funders']:
                                    paper_info['funders'].append(funder_info)
                        
                        if paper_info['funders']:  # Only add papers that have funders
                            papers_data[title] = paper_info
                    
                    # Sort papers by year and citations
                    sorted_papers = sorted(
                        papers_data.values(),
                        key=lambda x: (x['year'], x['citations']),
                        reverse=True
                    )
                    
                    # Display papers with their funders
                    papers_shown = 0
                    for paper in sorted_papers:
                        if papers_shown >= 15:  # Show top 4 papers
                            break
                            
                        # Paper title as main header (bold)
                        await ctx.send(f"**{paper['title']}**")
                        
                        # Year and citations on same line
                        stats = []
                        if paper['year']:
                            stats.append(f"Year: {paper['year']}")
                        if paper['citations']:
                            stats.append(f"Citations: {paper['citations']}")
                        if stats:
                            await ctx.send("   ".join(stats))
                        
                        # List funders
                        founders_shown = 0
                        for funder in paper['funders']:
                            if founders_shown >= 4:
                                break
                            founders_shown += 1
                            funder_line = funder['name']
                            if funder['grant_id']:
                                funder_line += f"\nGrant ID: {funder['grant_id']}"
                            await ctx.send(f"• {funder_line}")
                        
                        # Add paper link as a separate line
                        if paper['doi']:
                            await ctx.send(f"[View Publication →](https://doi.org/{paper['doi']})")
                        elif paper['id']:
                            await ctx.send(f"[View Publication →](https://openalex.org/{paper['id']})")
                        
                        # Add blank line between papers
                        if papers_shown < 10:  # Don't add blank line after last paper
                            await ctx.send("``` ```")
                        papers_shown += 1

                # Store paper details for quick reference
                paper_details = {}
                for item in enriched_data:
                    title = item.get('title', '')
                    if title:
                        paper_details[title] = {
                            'title': title,
                            'year': item.get('publication_year', ''),
                            'citations': item.get('cited_by_count', 0),
                            'doi': item.get('doi', ''),
                            'id': item.get('id', ''),
                            'abstract': item.get('abstract', ''),
                            'funders': [
                                {
                                    'name': grant.get('funder_display_name', ''),
                                    'grant_id': grant.get('award_id', ''),
                                    'details': grant.get('funder_details', {})
                                }
                                for grant in item.get('grants', [])
                                if grant.get('funder_display_name') not in ['Unknown Funder', 'N/A']
                            ]
                        }
                self.paper_details[channel_id] = paper_details

            except Exception as e:
                logger.error(f"Error in search command: {e}")
                await ctx.send(f"❌ An error occurred while searching: {str(e)}")

        @self.command(name="help")
        async def custom_help(ctx):
            """Show available commands"""
            commands_list = [
                "**🤖 PlutusAI - Your Research Funding Expert**",
                "",
                "I help researchers find and understand funding opportunities by analyzing research papers and their funding sources. I can maintain context across conversations and provide detailed insights about specific papers.",
                "",
                "**Available Commands:**",
                "",
                "🔍 **Search & Analysis**",
                "`!search <description>` - Search for funding opportunities based on your research description",
                "  Example: `!search research on RNA sequencing and gene expression analysis`",
                "",
                "💬 **Interactive Q&A**",
                "`!ask <question>` - Ask questions about search results, specific papers, or follow up on previous answers",
                "  Examples:",
                "  • `!ask What are the typical grant sizes for NIH funding in this area?`",
                "  • `!ask Tell me more about the paper on RNA sequencing`",
                "  • `!ask Which funding organization would be most suitable for my project?`",
                "  • `!ask What are the key requirements for these grants?`",
                "  • `!ask How does this compare to other funding sources?`",
                "",
                "👋 **Other Commands**",
                "`!hello` - Say hello and get started",
                "`!help` - Show this help message",
                "",
                "**Tips:**",
                "• Start with a detailed `!search` to find relevant funding opportunities",
                "• Use `!ask` to dive deeper into specific aspects of the results",
                "• I maintain conversation context for 30 minutes, so you can ask follow-up questions",
                "• I can provide detailed information about specific papers and their funding arrangements"
            ]
            await ctx.send("\n".join(commands_list))

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Game(name="!help for commands"))
        
        # Log guilds the bot is in
        guilds = self.guilds
        logger.info(f"Bot is in {len(guilds)} servers:")
        for guild in guilds:
            logger.info(f"- {guild.name} (ID: {guild.id})")
            # Log channels the bot can see in this guild
            channels = guild.channels
            logger.info(f"  Channels in {guild.name}:")
            for channel in channels:
                logger.info(f"  - {channel.name} (ID: {channel.id})")
        
        # Generate invite link with correct permissions
        invite_link = discord.utils.oauth_url(
            settings.discord_client_id,
            permissions=discord.Permissions(permissions=274878221312),
            scopes=["bot", "applications.commands"]
        )
        logger.info(f"Invite link: {invite_link}")
        
        # Send startup notification to the configured channel
        try:
            logger.info(f"Attempting to send startup message to channel ID: {settings.discord_channel_id}")
            await asyncio.sleep(2)  # Wait longer for connection to stabilize
            
            # Try to find the channel in any of the guilds
            target_channel = None
            for guild in self.guilds:
                for channel in guild.channels:
                    if str(channel.id) == settings.discord_channel_id:
                        target_channel = channel
                        break
                if target_channel:
                    break
            
            if target_channel:
                logger.info(f"Found channel '{target_channel.name}'")
                await target_channel.send("🟢 **Bot Restarted**\nThe bot has been restarted and is now online!")
                logger.info("Startup message sent successfully")
            else:
                logger.error(f"Could not find channel {settings.discord_channel_id}")
                logger.error("Please check:")
                logger.error("1. The bot is in the correct server")
                logger.error("2. The channel ID is correct")
                logger.error("3. The bot has permission to view and send messages in the channel")
        except discord.errors.Forbidden as e:
            logger.error(f"Permission error sending to channel {settings.discord_channel_id}: {e}")
        except discord.errors.NotFound as e:
            logger.error(f"Channel {settings.discord_channel_id} not found: {e}")
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")
            logger.error(f"Channel ID attempted: {settings.discord_channel_id}")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        # Only process commands if message starts with command prefix and hasn't been processed
        if message.content.startswith(self.command_prefix):
            await self.process_commands(message)
            return  # Return early to prevent double processing

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