
# LaptopFinder Nepal 💻📱🇳🇵

**An AI-powered laptop and phone recommendation platform built for the Nepali market.**

LaptopFinder Nepal helps users find suitable laptops and phones based on their budget, intended use, and preferred specifications. It combines machine learning, information retrieval, and a locally running AI assistant to make device shopping easier and more informed.

For laptop recommendations, the platform uses a dataset of 5,284 laptops with prices in Nepalese rupees (NPR). It ranks suitable options, explains why they match the user's requirements, supports side-by-side comparisons, and provides market insights through interactive visualizations.

## ✨ Features

### 🔍 Smart Recommendations
- Recommend suitable devices based on budget, intended use, and preferred specifications.
- Rank relevant laptop options using machine learning and recommendation logic.
- Support additional preferences such as RAM, storage, brand, processor, GPU tier, touchscreen, and dedicated graphics where applicable.
- Help users narrow down options without manually searching through large product listings.

### 🤖 AI Shopping Assistant
- Ask questions about laptops and phones through an AI-powered assistant.
- Use a locally running Mistral language model through Ollama.
- Retrieve relevant product information to provide context for AI-generated answers.
- Reduce reliance on paid cloud AI APIs by running the language model locally.

### 🧠 Retrieval-Augmented Generation (RAG)
- Use ChromaDB for vector storage and similarity-based retrieval.
- Retrieve relevant information from available product data.
- Provide the AI assistant with relevant context before generating responses.
- Help ground answers in the available dataset rather than relying entirely on the language model's general knowledge.

### ⚖️ Device Comparison
- Compare recommended devices side by side.
- Review important specifications and prices.
- Make more informed purchasing decisions based on individual requirements.

### 📊 Market Insights
- Explore charts and statistics derived from the product dataset.
- Analyze laptop prices, brands, and specifications.
- Use visualizations to better understand available options in the Nepali market.

### 🇳🇵 Built for Nepal
- Focus on laptop and phone buyers in Nepal.
- Present prices in Nepalese rupees (NPR).
- Help students, professionals, and everyday users find devices that suit their needs and budgets.

## 🧠 How It Works

1. **Enter Your Requirements:** Specify your budget, intended use, and preferred device specifications.
2. **Find Relevant Devices:** Retrieve products that match the selected criteria.
3. **Rank Recommendations:** Apply machine learning and recommendation logic to identify suitable options.
4. **Understand the Results:** Review device specifications, prices, and explanations for recommendations.
5. **Compare Devices:** Evaluate shortlisted products side by side.
6. **Ask the AI Assistant:** Ask follow-up questions using product information retrieved from the available dataset.
7. **Explore Market Data:** Review visualizations and statistics to understand the available options.

## 🛠️ Tech Stack

### Backend and Machine Learning
| Technology | Purpose |
|---|---|
| Python | Backend logic, machine learning, and data processing |
| FastAPI | REST API and backend services |
| scikit-learn | TF-IDF and machine learning utilities |
| ChromaDB | Vector storage and retrieval for RAG |
| Ollama | Local language model execution |
| Mistral | Language model for AI-assisted responses |
| pandas | Dataset manipulation and analysis |
| NumPy | Numerical operations |
| SQLite | Logging user interactions |

### Frontend
| Technology | Purpose |
|---|---|
| React | Interactive user interface |
| Vite | Frontend development and build tooling |
| JavaScript | Application logic and API integration |
| Recharts | Data visualization and charts |
| HTML and CSS | Page structure and styling |

### Testing and Development
| Technology | Purpose |
|---|---|
| pytest | Automated testing |
| Git | Version control |
| GitHub | Source code hosting and collaboration |

## 📂 Dataset

LaptopFinder Nepal uses structured product information to support recommendations, comparisons, and AI-assisted searches.

The laptop dataset contains **5,284 laptop records**, including prices in NPR and relevant product specifications.

The dataset supports:
- Product filtering and recommendation.
- Specification-based matching.
- Price and brand analysis.
- Retrieval of relevant product information for the AI assistant.

Phone recommendations are also supported by the platform. The exact dataset coverage and record count depend on the phone data source used by the project.

## 🚀 Getting Started

### Prerequisites

Make sure the following tools are installed:

- Python
- Node.js and npm
- Ollama
- Git
- A compatible local language model, such as Mistral

### 1. Clone the Repository

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_PROJECT_FOLDER
```

### 2. Set Up the Backend

Create and activate a Python virtual environment:

```bash
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

Install the backend dependencies using the project's dependency file. For example, if it includes `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Set Up Ollama

Install Ollama and download the required language model:

```bash
ollama pull mistral
```

Make sure Ollama is running and that the model name matches the configuration used by the application.

### 4. Start the Backend

For a FastAPI application with `app/main.py` as its entry point, the command would be:

```bash
uvicorn app.main:app --reload
```

The actual module path may differ depending on the repository structure.

Once the backend is running, FastAPI commonly provides interactive API documentation at:

```text
http://localhost:8000/docs
```

### 5. Set Up the Frontend

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local URL displayed in the terminal to access the application.

> **Note:** The directory names, backend entry point, dependency files, and environment configuration above are examples. Adjust them to match the actual repository. The backend, frontend, and Ollama service must be configured to communicate with one another.

## 🧪 Testing

The project uses pytest for automated testing.

If the repository contains a configured test suite, run:

```bash
pytest
```

Additional tests can cover recommendation logic, API endpoints, data retrieval, and response handling.

## 🔐 Local AI and Data Grounding

LaptopFinder Nepal uses Ollama to run its language model locally, reducing dependence on external AI services.

Its RAG workflow retrieves relevant product information before the language model generates a response. This helps make answers more relevant to the available dataset.

However, retrieval does not guarantee that every AI response will be factually correct. Product availability, prices, and specifications should be verified before making a purchase.

## 💡 What Makes LaptopFinder Nepal Different?

Many shopping platforms present users with long lists of products and leave them to determine which option is best.

LaptopFinder Nepal aims to make that process more useful by combining:

- **Personalized recommendations** based on budgets and requirements.
- **Explainable results** that help users understand why a product is recommended.
- **Dataset-grounded AI assistance** using retrieval and a locally running language model.
- **Device comparisons and market insights** to support informed decisions.
- **A Nepal-focused approach** using prices in NPR.

The goal is to help people make more confident device-buying decisions without needing to be technology experts.

## 🔮 Future Improvements

Potential areas for further development include:

- More comprehensive phone and laptop datasets.
- Improved recommendation evaluation and ranking.
- More detailed comparisons across device categories.
- Price tracking and historical price analysis.
- More robust evaluation of AI response accuracy.
- Expanded Nepali-language support.

## 👩‍💻 Author

**Garima Dangol**

- GitHub: [garimadangool](https://github.com/garimadangool)
- LinkedIn: [Garima Dangol](https://np.linkedin.com/in/garima-dangol-78b0b9368)

---

*Built to make finding the right laptop or phone in Nepal simpler, smarter, and more transparent.*
