#  ArXiv Intelligent Paper Assistant (PaperLens)

A comprehensive RAG (Retrieval-Augmented Generation) system that crawls ArXiv papers, learns user preferences, and provides intelligent paper recommendations with multimodal Q&A capabilities.

##  Features

- **Daily ArXiv Crawling**: Automatically fetch papers based on user interests
- **Intelligent Recommendations**: Machine learning-powered paper suggestions
- **Multimodal RAG**: Chat with papers using text and images via Gemini Pro
- **User Interaction Tracking**: Like, dislike, save, and delete papers
- **Multi-Channel Notifications**: Email and Telegram integration
- **Vector Search**: FAISS-powered semantic search across papers
- **Personalized Experience**: Adaptive recommendations based on user feedback

##  Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ArXiv API     │───▶│  Daily Crawler  │───▶│   Vector DB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Email/Telegram  │◀───│  Notification   │    │  RAG System     │
│   Notifications │    │    Service      │    │ (Gemini Pro)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                              ┌─────────────────┐    ┌─────────────────┐
                              │  User Feedback  │◀───│   Frontend UI   │
                              │    Learning     │    │                 │
                              └─────────────────┘    └─────────────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.9+
- Docker (optional)
- Google API Key (for Gemini)
- Telegram Bot Token (optional)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd arxiv-rag-system
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Environment variables**
   ```bash
   export GOOGLE_API_KEY="your-gemini-api-key"
   export TELEGRAM_BOT_TOKEN="your-bot-token"  # optional
   export EMAIL_PASSWORD="your-email-password"  # optional
   ```

4. **Initialize database**
   ```bash
   python scripts/init_db.py
   python scripts/seed_user.py
   ```

##  Quick Start

1. **Start the crawler** (runs daily)
   ```bash
   python scripts/run_agents.py
   ```

2. **Launch the backend**
   ```bash
   cd backend
   python -m app.main
   ```

3. **Interact with papers**
   ```python
   from agents.system_agents.papers_rag import GeminiProAgent, ScientificPaperRetriever
   
   # Initialize RAG system
   retriever = ScientificPaperRetriever()
   agent = GeminiProAgent(api_key="your-key")
   
   # Ask questions about papers
   query = "What are the main contributions of this paper?"
   results = retriever.retrieve_all(query, text_top_k=5, image_top_k=3)
   response = agent.generate_response(query, results)
   
   print(response["answer"])
   ```

##  Project Structure

```
├── agents/                 # Core AI agents
│   ├── system_agents/     # Main system agents
│   │   ├── crawler.py     # ArXiv paper crawler
│   │   └── papers_rag.py  # Multimodal RAG system
│   ├── data/              # Data processing & embeddings
│   ├── tools/             # Utility tools
│   └── prompts/           # LLM prompts
├── backend/               # FastAPI backend
│   └── app/
│       ├── models/        # Database models
│       ├── routes/        # API endpoints
│       └── services/      # Business logic
├── faiss_index/          # Vector database indices
├── storage/              # Paper storage
│   ├── raw/              # Original PDFs
│   └── processed/        # Extracted text & images
└── scripts/              # Utility scripts
```



## 🤖 Available Agents

### 1. ArXiv Crawler
- Fetches papers daily based on user interests
- Processes PDFs and extracts text/images
- Updates vector database with new embeddings

### 2. RAG Assistant
- Answers questions using retrieved context
- Supports both text and image understanding
- Powered by Google's Gemini Pro model

### 3. Recommendation Engine
- Learns from user interactions (likes/dislikes)
- Provides personalized paper suggestions
- Adapts over time based on feedback

## 📊 Features in Detail

### Multimodal RAG
- **Text Retrieval**: Semantic search through paper content
- **Image Understanding**: Process figures, charts, and diagrams
- **Context-Aware**: Combines visual and textual information
- **Citation Support**: References sources in responses

### User Learning
- **Implicit Feedback**: Tracks reading time, interactions
- **Explicit Feedback**: Likes, dislikes, saves, deletes
- **Preference Evolution**: Updates user profiles over time
- **Cold Start**: Handles new users with category-based recommendations

### Notification System
- **Email Digest**: Daily/weekly paper summaries
- **Telegram Bot**: Real-time paper alerts
- **Customizable**: User-controlled frequency and topics

## 🛠️ Development

### Running Tests
```bash
python -m pytest agents/test/
```

### Adding New Features
1. Create new agents in `agents/system_agents/`
2. Add database models in `backend/app/models/`
3. Implement API endpoints in `backend/app/routes/`
4. Update configuration in `agents/config.py`

### Docker Deployment
```bash
docker build -t arxiv-rag .
docker run -p 8000:8000 arxiv-rag
```

## 📈 Performance

- **Vector Search**: Sub-second retrieval with FAISS
- **Daily Processing**: 50+ papers in < 5 minutes
- **Multimodal QA**: ~2-3 seconds response time
- **Storage**: Efficient PDF processing and compression

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- Create an issue for bug reports or feature requests
- Check existing issues before creating new ones
- Provide detailed information for faster resolution

---

**Built with ❤️ for the research community**