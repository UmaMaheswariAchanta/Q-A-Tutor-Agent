# Network Security Q&A Tutor Agent

A comprehensive AI-powered Q&A chatbot and quiz system for Network Security course materials. This application provides intelligent answers to questions based on lecture slides, textbooks, and course materials, with the ability to generate interactive quizzes to test knowledge.

## 🎯 Project Overview

This project is an on-demand Q&A tutor agent that:
- Answers Network Security course questions using local, private data
- Generates interactive quizzes with multiple-choice and true/false questions
- Provides citations and references from course materials
- Falls back to internet search when answers aren't found in local documents
- Runs entirely on a local machine, ensuring data security and privacy

## ✨ Features

### Q&A Chatbot
- **Intelligent Question Answering**: Uses local LLM (GPT4All) to generate context-aware responses
- **Document Retrieval**: Searches through course materials using semantic similarity
- **Citation Support**: Provides document names, page numbers, and references
- **Internet Fallback**: Automatically searches the web when local documents don't contain the answer
- **Modern UI**: Beautiful, responsive web interface with animated backgrounds

### Quiz Agent
- **AI-Generated Questions**: Creates multiple-choice and true/false questions automatically
- **Interactive Interface**: User-friendly radio button interface with visual feedback
- **Instant Feedback**: Provides immediate results with explanations
- **Score Tracking**: Shows overall score and per-question results
- **Topic-Based Generation**: Generate questions on specific topics or random topics

## 📋 Prerequisites

Before installing, ensure you have:

- **Python 3.9 or higher** (Python 3.10+ recommended)
- **Git** (for version control)
- **4GB+ RAM** (for running the local LLM, 8GB+ recommended)
- **2GB+ free disk space** (for models and database)
- **Internet connection** (for initial setup and optional web search feature)

### System Requirements

- **Operating System**: Windows, Linux, or macOS
- **Python**: 3.9, 3.10, 3.11, or 3.12 (3.14 requires special pydantic installation)
- **RAM**: Minimum 4GB, Recommended 8GB+ for better performance
- **Storage**: 2GB+ for models and database
- **CPU**: Any modern CPU (GPU optional, not required)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd NS_GP1_ondemand_Q-A-main
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If you're using Python 3.14, install pydantic first:
```bash
pip install "pydantic>=2.12.0"
pip install -r requirements.txt
```

### 4. Download LLM Model

You need to download a compatible LLM model. The application supports GPT4All models in `.gguf` format.

**Option 1: Download from GPT4All**
- Visit [GPT4All Model Hub](https://gpt4all.io/index.html)
- Download a compatible model (e.g., `Meta-Llama-3-8B-Instruct.Q4_0.gguf` or `phi-2.Q4_0.gguf`)
- Place it in the `models/` directory

**Option 2: Use Existing Model**
- If you already have a model, update the model path in the application files

### 5. Set Up ChromaDB

ChromaDB is used for vector storage and retrieval. It will be automatically initialized when you first run the application.

### 6. Configure Environment Variables (Optional)

Create a `.env` file or set environment variables:

```bash
# For web search functionality (optional)
SERPAPI_API_KEY=your_serpapi_key_here

# For LM Studio integration (if using LM Studio instead of GPT4All)
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_API_KEY=lm-studio
```

To get a SERPAPI key:
1. Visit [SerpAPI](https://serpapi.com/)
2. Sign up for a free account
3. Copy your API key

## 📁 Project Structure

```
NS_GP1_ondemand_Q-A-main/
│
├── Scripts/
│   ├── chatbot_application.py      # Main Q&A chatbot application
│   ├── Quiz_Agent.py               # Quiz generation and evaluation
│   ├── Data_insertion_chromadb.py  # Script to insert PDFs into ChromaDB
│   ├── Data_insertion_qdrant.py    # Script to insert PDFs into Qdrant (alternative)
│   ├── initialise_chromadb.py      # Initialize ChromaDB collection
│   └── initialise_qdrant.py        # Initialize Qdrant collection (alternative)
│
├── templates/
│   ├── index.html                  # Q&A chatbot web interface
│   └── quiz.html                   # Quiz web interface
│
├── References/                      # Course materials (PDFs)
│   ├── Lecture 1_slides.pdf
│   ├── Lecture 2_slides.pdf
│   └── ...
│
├── chroma_db/                      # ChromaDB database (auto-generated)
├── models/                         # LLM model files
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🔧 Configuration

### Update Model Path

Edit the model path in the application files:

**For Q&A Chatbot** (`Scripts/chatbot_application.py`):
```python
model_path = "Meta-Llama-3-8B-Instruct.Q4_0.gguf"  # Update this path
```

**For Quiz Agent** (`Scripts/Quiz_Agent.py`):
```python
model_path = r"C:\Users\YourName\path\to\model.gguf"  # Update this path
```

### Configure Database

The application uses ChromaDB by default. The database is automatically created in the `chroma_db/` directory.

### Adjust Relevance Threshold

In `Scripts/chatbot_application.py`, you can adjust the relevance threshold:
```python
relevance_threshold = 0.4  # Lower = more results, Higher = more relevant results
```

## ⚡ Quick Start

For a quick start, follow these steps:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Download a model** and place it in the `models/` directory

3. **Insert documents** (if not done already):
   ```bash
   python Scripts/Data_insertion_chromadb.py
   ```

4. **Run the chatbot**:
   ```bash
   python Scripts/chatbot_application.py
   ```
   
5. **Open browser**: Navigate to `http://127.0.0.1:7860`

## 📚 Detailed Usage

### Step 1: Prepare Course Materials

1. Place all your PDF course materials in the `References/` directory
2. Ensure PDFs are readable and well-formatted

### Step 2: Initialize Database

```bash
cd Scripts
python initialise_chromadb.py
```

### Step 3: Insert Documents into Database

**Important**: Before running the data insertion script, update the PDF path in `Scripts/Data_insertion_chromadb.py`:

Edit the file and update the `pdf_path` variable at the bottom:

```python
# In Scripts/Data_insertion_chromadb.py, line ~85
pdf_path = r"C:\Users\YourName\path\to\References"  # Update this path
# Or use a relative path:
# pdf_path = Path(__file__).parent.parent / "References"
```

Then run:

```bash
python Scripts/Data_insertion_chromadb.py
```

This script will:
- Process all PDFs in the specified directory
- Extract text from each page
- Generate embeddings using Sentence Transformers
- Store them in ChromaDB with metadata (document name, page number)

**Note**: 
- The script processes PDFs recursively if subdirectories exist
- Large PDFs may take time to process
- Progress will be shown in the terminal

### Step 4: Run the Q&A Chatbot

```bash
python Scripts/chatbot_application.py
```

The application will start on `http://127.0.0.1:7860`

Open your browser and navigate to:
```
http://127.0.0.1:7860
```

### Step 5: Run the Quiz Agent

**Note**: The Quiz Agent uses the same port (7860) as the chatbot by default. If you want to run both simultaneously, you'll need to change the port in `Quiz_Agent.py`.

To run the Quiz Agent:

```bash
python Scripts/Quiz_Agent.py
```

The quiz application will start on `http://127.0.0.1:7860`

**To run both applications simultaneously**, edit `Scripts/Quiz_Agent.py` and change the port:
```python
uvicorn.run(app, host="127.0.0.1", port=7861)  # Use a different port
```

Then open your browser and navigate to:
```
http://127.0.0.1:7860  # Q&A Chatbot
http://127.0.0.1:7861  # Quiz Agent (if using different port)
```

## 🎮 How to Use

### Q&A Chatbot

1. **Enter Your Question**: Type your question in the input field on the left panel
2. **Submit**: Click "Ask Question" button
3. **View Response**: 
   - Answer appears in the right panel
   - Sources and citations are displayed below the answer
   - If the answer comes from internet, web references are provided

### Quiz Agent

1. **Generate Questions**: 
   - Optionally enter a topic (e.g., "firewalls", "encryption")
   - Click "Generate 5 Questions"
   
2. **Answer Questions**:
   - Read each question carefully
   - Select your answer using the radio buttons
   - Selected answers are highlighted in blue
   
3. **Submit Quiz**:
   - Click "Submit Answers" when all questions are answered
   - All questions must be answered before submission
   
4. **View Results**:
   - See your overall score
   - Review correct and incorrect answers
   - Read explanations for each question

## 🔌 API Endpoints

### Q&A Chatbot API

- `GET /` - Main chat interface
- `POST /query` - Query endpoint (JSON API)
- `POST /query-form` - Query endpoint (Form submission)

### Quiz Agent API

- `GET /` - Quiz home page
- `POST /generate` - Generate quiz questions
- `POST /submit-quiz` - Submit quiz answers

## 🛠️ Troubleshooting

### Issue: Model not found

**Solution**: 
- Ensure the model file is in the correct directory
- Update the model path in the application file
- Verify the model file name matches exactly

### Issue: ChromaDB errors

**Solution**:
- Delete the `chroma_db/` directory and reinitialize
- Run `python Scripts/initialise_chromadb.py` again
- Check file permissions

### Issue: PDF parsing errors

**Solution**:
- Ensure PDFs are not corrupted
- Check if PDFs are password-protected
- Verify PDFs are readable text (not just images)
- Clean PDFs before processing

### Issue: Slow response times

**Solution**:
- Use a smaller, faster model (e.g., `phi-2.Q4_0.gguf`)
- Reduce the number of retrieved documents
- Increase the relevance threshold
- Ensure adequate RAM is available

### Issue: Port already in use

**Solution**:
- Change the port number in the application file:
  ```python
  uvicorn.run(app, host="127.0.0.1", port=7861)  # Change port number
  ```

### Issue: Import errors

**Solution**:
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt --upgrade`
- Check Python version: `python --version` (should be 3.9+)

### Issue: Internet search not working

**Solution**:
- Verify SERPAPI_API_KEY is set correctly
- Check internet connection
- Verify API key is valid and has credits

## 🔒 Security & Privacy

- **Local Processing**: All data processing happens on your local machine
- **No Data Transmission**: Questions and answers are not sent to external servers (except optional web search)
- **Private Database**: All course materials are stored locally in ChromaDB
- **Offline Capability**: The chatbot works offline (except for web search feature)

## 📊 System Architecture

```
User Query
    ↓
Sentence Transformer (Embedding)
    ↓
ChromaDB (Vector Search)
    ↓
Retrieve Relevant Documents
    ↓
GPT4All (LLM)
    ↓
Generate Answer + Citations
    ↓
Display Response
```

## 🔮 Future Improvements

- [ ] Enhanced UI with follow-up questions
- [ ] Performance optimization for faster responses
- [ ] Ambiguity handling for unclear queries
- [ ] Support for multiple file formats (DOCX, TXT, etc.)
- [ ] User authentication and session management
- [ ] Export quiz results to PDF
- [ ] Support for image-based questions
- [ ] Multi-language support
- [ ] Advanced analytics and usage statistics

## 📝 Notes

- The application uses **GPT4All** for local LLM processing
- **ChromaDB** is used for vector storage and retrieval
- **Sentence Transformers** is used for generating embeddings
- **FastAPI** is used as the web framework
- **Jinja2** is used for template rendering

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is for educational purposes.

## 👥 Authors

Network Security - Group 1

## 🙏 Acknowledgments

- GPT4All for local LLM capabilities
- ChromaDB for vector database
- Sentence Transformers for embeddings
- FastAPI for web framework
- All open-source contributors

## 📞 Support

For issues and questions:
1. Check the Troubleshooting section
2. Review the code comments
3. Check existing GitHub issues
4. Create a new issue with detailed information

## 🔄 Version History

- **v1.0** - Initial release with Q&A chatbot and Quiz agent
- Features: Document retrieval, quiz generation, web search fallback

---

**Happy Learning! 🎓**

