import aiohttp

# Dictionary to store search results per user
user_search_results = {}

@bot.command(name='search')
async def search(ctx, *, query):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8000/search', json={
                'query': query
            }) as response:
                if response.status == 200:
                    search_results = await response.json()
                    # Store the raw JSON response
                    user_search_results[ctx.author.id] = search_results
                    await ctx.send("Search completed. You can now ask questions about the results.")
                else:
                    await ctx.send(f"Error: Search failed. Status code: {response.status}")
    except Exception as e:
        await ctx.send(f"An error occurred during search: {str(e)}")

@bot.command(name='ask')
async def ask(ctx, *, question):
    try:
        # Check if user has previous search results
        if ctx.author.id not in user_search_results:
            await ctx.send("Please perform a !search first before asking a question.")
            return
            
        # Get the stored search results for this user
        search_context = user_search_results[ctx.author.id]
        
        # Prepare the payload with both context and question
        payload = {
            'context': search_context['results'] if 'results' in search_context else search_context,
            'question': question
        }
        
        # Send request to ask endpoint
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8000/ask', json=payload) as response:
                if response.status == 200:
                    answer_data = await response.json()
                    if 'answer' in answer_data:
                        await ctx.send(f"Answer: {answer_data['answer']}")
                    else:
                        await ctx.send(f"Error: Unexpected response format")
                else:
                    await ctx.send(f"Error: Unable to get answer. Status code: {response.status}")
                    
    except Exception as e:
        await ctx.send(f"An error occurred while processing your question: {str(e)}")