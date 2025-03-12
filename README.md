# PlutusAI: Research Funding Assistant

PlutusAI is an intelligent research funding assistant that helps researchers and academics identify relevant funding opportunities by analyzing academic papers and grant patterns. Using advanced AI and academic databases, it provides data-driven insights and strategic recommendations to increase your chances of securing research funding.

![PlutusAI Demo](public/demo.gif)

## 🌟 Features

- **Intelligent Search Analysis**: Automatically extracts and analyzes relevant search terms from project descriptions
- **Comprehensive Funding Data**: Identifies funding patterns and opportunities from academic papers and grants
- **Strategic Recommendations**: Provides tailored funding strategies and insights
- **Multi-Platform Support**: Access via web interface or Discord bot
- **Real-Time Updates**: Stream processing status with server-sent events
- **Beautiful UI**: Modern, responsive interface with intuitive visualizations

## 🚀 Getting Started

### Prerequisites

- Node.js (v18 or higher)
- Python (v3.9 or higher)
- Redis server
- Discord bot token (optional, for Discord integration)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/plutusai.git
cd plutusai
```

2. Set up the Python API:
```bash
cd python-api
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Set up the Next.js frontend:
```bash
cd ../nextjs-app
npm install
```

### Configuration

Create a `.env` file in the `python-api` directory with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_discord_channel_id
REDIS_URL=redis://localhost:6379
```

### Running the Application

1. Start the Redis server:
```bash
redis-server
```

2. Start the Python API (from python-api directory):
```bash
uvicorn app.main:app --reload
```

3. Start the Next.js frontend (from nextjs-app directory):
```bash
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- API: https://plutusai-api.onrender.com

## 🛠️ Architecture

### Frontend (Next.js)
- Modern React application with server-side rendering
- Real-time updates using Server-Sent Events
- Tailwind CSS for styling
- TypeWriter effects for dynamic content

### Backend (FastAPI)
- Asynchronous API with FastAPI
- OpenAI integration for intelligent analysis
- OpenAlex API for academic paper analysis
- Redis caching for improved performance
- Discord bot integration

## 📚 API Documentation

### Main Endpoints

- `GET /generate_funding_report`: Generate a funding report
  - Query Parameters:
    - `description`: Project description text
  - Returns: Server-Sent Events stream with report generation progress

- `POST /discord/send`: Send a message to Discord
  - Query Parameters:
    - `message`: Message text to send
  - Returns: Success/failure status

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for their powerful language models
- OpenAlex for academic paper data
- Discord for bot integration capabilities
- The open-source community for various tools and libraries used in this project
