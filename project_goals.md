# Project Ground Truth Summary

## Project Name
Synthetic Data Generation Agent Framework for LLM Post-Training

## Primary Objective
Build an autonomous, multi-agent system that generates high-quality synthetic datasets for training and fine-tuning large language models. The system should support multiple post-training paradigms and produce production-ready training data across various domains.

## What This System Does

### Core Functionality
The system takes a user request like "Generate 1000 chemistry SFT examples" and autonomously:

1. **Clarifies Requirements**: Asks questions to understand exactly what the user needs
2. **Plans Execution**: Creates a detailed strategy for data generation
3. **Generates Questions**: Creates domain-specific questions that need answering
4. **Conducts Research**: Gathers ground truth information from authoritative sources
5. **Generates Training Data**: Creates synthetic examples using research context
6. **Reviews Quality**: Validates accuracy and scores each generated example
7. **Stores Results**: Saves production-ready data to appropriate database tables

### Supported Training Types
The system generates data for 9 different LLM post-training methods:
- **SFT** (Supervised Fine-Tuning): Instruction-response pairs
- **DPO** (Direct Preference Optimization): Chosen vs rejected response pairs
- **PPO** (Proximal Policy Optimization): Responses with reward signals
- **GRPO** (Group Relative Policy Optimization): Reasoning chains with verifiable answers
- **RLHF** (Reinforcement Learning from Human Feedback): Human preference comparisons
- **KTO** (Kahneman-Tversky Optimization): Binary good/bad feedback
- **ORPO** (Odds Ratio Preference Optimization): Combined SFT + preference data
- **Chat**: Multi-turn conversations
- **QA**: Question-answer pairs with reasoning

## Key Design Principles

### 1. Agent-Based Architecture
Using Google's Agent Development Kit (ADK), the system is built as a hierarchy of specialized agents:
- **Orchestrator**: Coordinates the entire workflow
- **Planning Agent**: Creates execution strategies
- **Question Agent**: Generates domain questions
- **Research Agent**: Gathers authoritative context
- **Generation Agent**: Creates synthetic training data
- **Reviewer Agent**: Validates quality and accuracy

### 2. Quality Over Quantity
- Ground truth research from authoritative sources
- Multi-stage validation and review
- Code execution verification for technical content
- Independent fact-checking via web search
- Quality scoring for every generated example

### 3. Domain Flexibility
The system is designed to be domain-agnostic and support a wide range of subjects:

**STEM Fields**:
- **Chemistry**: Organic, analytical, inorganic, physical chemistry, biochemistry
- **Mathematics**: Algebra, calculus, statistics, proofs, number theory, topology
- **Physics**: Classical mechanics, quantum mechanics, thermodynamics, electromagnetism
- **Biology**: Molecular biology, genetics, ecology, anatomy, microbiology
- **Computer Science**: Algorithms, data structures, systems design, theory
- **Engineering**: Mechanical, electrical, civil, chemical, software engineering
- **Data Science**: Statistics, machine learning, data analysis, visualization

**Programming & Technology**:
- **Languages**: Python, TypeScript, Rust, C#, C++, Java, JavaScript, Go, SQL
- **Frameworks**: React, Node.js, Django, Flask, TensorFlow, PyTorch
- **DevOps**: Docker, Kubernetes, CI/CD, cloud platforms (AWS, GCP, Azure)
- **Web Development**: Frontend, backend, full-stack, APIs, databases
- **Mobile Development**: iOS, Android, cross-platform

**Humanities & Social Sciences**:
- **History**: World history, regional history, historical analysis
- **Literature**: Literary analysis, creative writing, poetry, prose
- **Philosophy**: Logic, ethics, metaphysics, epistemology
- **Psychology**: Cognitive, developmental, social, clinical psychology
- **Economics**: Microeconomics, macroeconomics, econometrics, game theory
- **Political Science**: Comparative politics, international relations, public policy
- **Sociology**: Social theory, research methods, cultural studies

**Professional & Business**:
- **Business**: Management, strategy, operations, entrepreneurship
- **Finance**: Corporate finance, investment, accounting, financial modeling
- **Marketing**: Digital marketing, brand strategy, consumer behavior
- **Law**: Contract law, corporate law, intellectual property, case analysis
- **Medicine**: Clinical reasoning, diagnostics, treatment protocols, medical ethics

**Creative & Applied**:
- **Design**: UI/UX, graphic design, product design, design thinking
- **Music**: Music theory, composition, performance, music history
- **Art**: Art history, techniques, criticism, visual arts
- **Architecture**: Design principles, structural analysis, architectural history
- **Linguistics**: Syntax, semantics, phonology, language acquisition

**Interdisciplinary**:
- **Environmental Science**: Climate, ecology, sustainability, conservation
- **Neuroscience**: Brain function, cognitive neuroscience, neuroanatomy
- **Bioinformatics**: Computational biology, genomics, proteomics
- **Artificial Intelligence**: Machine learning, NLP, computer vision, reinforcement learning
- **Robotics**: Control systems, kinematics, perception, planning

The system should easily extend to **any domain** where factual knowledge can be researched and structured training data can be generated.

## Model Selection Strategy

The system uses different Gemini models strategically based on task complexity and requirements:

### gemini-3-pro-preview (Complex Reasoning & Delegation)
**Use for agents requiring**:
- Extensive multi-step reasoning
- Strategic planning and decision-making
- Complex task delegation
- Nuanced understanding of requirements
- Sophisticated context integration

**Agents using this model**:
- **Orchestrator Agent**: Coordinates workflow, makes high-level decisions
- **Planning Agent**: Creates complex execution strategies
- **Generation Agent** (for complex domains): Generates reasoning chains, handles multi-step problems
- **Reviewer Agent** (for complex validation): Deep quality analysis, reasoning verification

**Rationale**: These agents need the deepest reasoning capabilities to make intelligent decisions about workflow, understand user intent, and generate sophisticated content.

### gemini-2.5-flash (Standard Operations)
**Use for agents requiring**:
- Fast information retrieval
- Web search and data extraction
- Straightforward text processing
- Context synthesis
- Standard Q&A tasks

**Agents using this model**:
- **Research Agent**: Web searches, content extraction, basic synthesis
- **Question Agent**: Question generation from topics
- **Database Agent**: Query construction, data management
- **Generation Agent** (for simple domains): Basic SFT, straightforward Q&A

**Rationale**: These tasks are important but don't require the deepest reasoning. Flash provides speed and efficiency for high-volume operations.

### gemini-2.0-flash (Fast Validation & Formatting)
**Use for agents requiring**:
- Quick validation checks
- Format compliance verification
- Basic quality scoring
- Simple transformations

**Agents using this model**:
- **Reviewer Agent** (for basic checks): Format validation, basic quality metrics
- **Data Export**: Format conversion, output generation

**Rationale**: These are fast, deterministic operations where speed matters more than deep reasoning.

### Selection Heuristic

```
If task requires:
  - Multi-step reasoning → gemini-3-pro-preview
  - Complex domain expertise → gemini-3-pro-preview
  - Strategic decision-making → gemini-3-pro-preview
  - Fast data retrieval → gemini-2.5-flash
  - Web search operations → gemini-2.5-flash
  - Simple validation → gemini-2.0-flash
```

**Cost-Effectiveness**: This tiered approach balances quality with cost. The most capable pro model is used only where deep reasoning is essential, while faster, cheaper models handle the bulk of operations.

## MCP Servers & External Data Sources

The system integrates with external data sources through MCP (Model Context Protocol) servers and specialized tools to access high-quality, openly licensed content for research and training data generation.

### arXiv Family (Open Access Preprints)

**Primary MCP Server**: arXiv MCP Server
- **Purpose**: Access scientific preprints across all disciplines
- **License**: Most papers under CC-BY or similar permissive licenses
- **Capabilities**:
  - Search by topic, author, category, date range
  - Retrieve full-text PDFs and metadata
  - Access LaTeX source files (often available)
  - Extract citations and references

**arXiv Categories by Domain**:
- **Physics**: astro-ph, cond-mat, gr-qc, hep-ex, hep-lat, hep-ph, hep-th, math-ph, nlin, nucl-ex, nucl-th, physics, quant-ph
- **Mathematics**: math (all subcategories)
- **Computer Science**: cs.AI, cs.CL, cs.CV, cs.LG, cs.NE, cs.RO, etc.
- **Statistics**: stat.AP, stat.CO, stat.ME, stat.ML, stat.TH
- **Quantitative Biology**: q-bio
- **Quantitative Finance**: q-fin
- **Economics**: econ
- **Electrical Engineering**: eess

### Related rxiv Sites (Domain-Specific Preprints)

**chemRxiv** (Chemistry)
- **URL**: chemrxiv.org
- **License**: CC-BY-NC-ND 4.0 (verify per paper)
- **Content**: Chemistry preprints, preregistrations
- **API**: Available for programmatic access

**bioRxiv** (Biology)
- **URL**: biorxiv.org
- **License**: CC-BY, CC-BY-NC, CC-BY-ND, CC0 (varies)
- **Content**: Biology and life sciences preprints
- **API**: Yes, full API access

**medRxiv** (Medicine)
- **URL**: medrxiv.org
- **License**: CC-BY, CC-BY-NC, CC-BY-ND (varies)
- **Content**: Clinical and health sciences
- **API**: Yes, shares infrastructure with bioRxiv

**SocArXiv** (Social Sciences)
- **URL**: osf.io/preprints/socarxiv
- **License**: Various CC licenses
- **Content**: Social sciences preprints

**PsyArXiv** (Psychology)
- **URL**: psyarxiv.com
- **License**: Various CC licenses
- **Content**: Psychological sciences

**EarthArXiv** (Earth Sciences)
- **URL**: eartharxiv.org
- **License**: Various CC licenses
- **Content**: Earth sciences, geosciences

**engrXiv** (Engineering)
- **URL**: engrxiv.org
- **License**: Various CC licenses
- **Content**: Engineering preprints

**SportRxiv** (Sport Sciences)
- **URL**: sportrxiv.org
- **License**: Various CC licenses
- **Content**: Sport and exercise science

### Open Access Publishers & Repositories

**PubMed Central (PMC)**
- **URL**: ncbi.nlm.nih.gov/pmc
- **License**: Many open access articles with CC licenses
- **Content**: Biomedical and life sciences literature
- **API**: E-utilities API for programmatic access
- **MCP Server**: Could integrate with existing PubMed MCP

**PLOS (Public Library of Science)**
- **URL**: plos.org
- **License**: CC-BY 4.0 (all content)
- **Content**: Biology, medicine, and related fields
- **API**: Search and article APIs available

**MDPI (Multidisciplinary Digital Publishing Institute)**
- **URL**: mdpi.com
- **License**: CC-BY 4.0 for most journals
- **Content**: Multidisciplinary science journals
- **API**: Available

**Frontiers**
- **URL**: frontiersin.org
- **License**: CC-BY (most content)
- **Content**: Multidisciplinary peer-reviewed journals
- **API**: Available

**SpringerOpen**
- **URL**: springeropen.com
- **License**: CC-BY (most content)
- **Content**: Multidisciplinary open access
- **API**: Springer API access

**IEEE Open Access**
- **URL**: ieee.org/publications/open-access
- **License**: Various, many CC-BY
- **Content**: Engineering, computer science, electronics

**arXiv Vanity** (Rendered arXiv Papers)
- **URL**: arxiv-vanity.com
- **Purpose**: HTML rendered versions of arXiv papers
- **Easier parsing**: Better than PDF extraction

### Educational & Reference Materials

**Wikipedia**
- **URL**: wikipedia.org
- **License**: CC-BY-SA 3.0
- **Content**: Encyclopedia articles across all domains
- **API**: MediaWiki API (comprehensive)
- **MCP Integration**: Existing Wikipedia MCP servers available

**Wikibooks**
- **URL**: wikibooks.org
- **License**: CC-BY-SA 3.0
- **Content**: Free textbooks and educational resources

**Khan Academy**
- **URL**: khanacademy.org
- **License**: CC-BY-NC-SA (most content)
- **Content**: Educational videos and exercises
- **API**: Available for some content

**OpenStax**
- **URL**: openstax.org
- **License**: CC-BY 4.0
- **Content**: Free, peer-reviewed textbooks
- **Formats**: PDF, web, various ebook formats

**MIT OpenCourseWare**
- **URL**: ocw.mit.edu
- **License**: CC-BY-NC-SA
- **Content**: MIT course materials
- **API**: Limited

**Coursera Open Content**
- **License**: Some courses offer CC-licensed materials
- **Content**: Educational course materials

### HuggingFace Integration

**HuggingFace Hub**
- **URL**: huggingface.co
- **Purpose**: Dataset repository and model hub
- **License**: Varied (filter by license)

**Use Cases**:
1. **Existing Datasets for Augmentation**:
   - Browse datasets by domain (code, math, science, etc.)
   - Filter by permissive licenses (Apache-2.0, MIT, CC-BY)
   - Download and combine with synthetic data
   - Example: combine synthetic chemistry data with existing datasets

2. **Training Data Templates**:
   - Study structure of existing high-quality datasets
   - Use as templates for synthetic generation
   - Ensure compatibility with popular training frameworks

3. **Dataset Hosting**:
   - Upload generated synthetic datasets
   - Version control for iterations
   - Community feedback and usage tracking
   - Standard format (datasets library compatible)

4. **Model Testing**:
   - Quick validation of generated data quality
   - Fine-tune small models on synthetic data
   - Compare against baselines

**HuggingFace Datasets MCP Server**:
```python
# Integration with HuggingFace
from datasets import load_dataset

# Load existing datasets for templates
dataset = load_dataset("codeparrot/github-code", split="train")

# Upload synthetic data
from huggingface_hub import HfApi
api = HfApi()
api.upload_file(
    path_or_fileobj="synthetic_chemistry_sft.jsonl",
    path_in_repo="data/train.jsonl",
    repo_id="username/synthetic-chemistry-sft",
    repo_type="dataset"
)
```

**Key HuggingFace Datasets to Reference**:
- **Code**: codeparrot/github-code, bigcode/the-stack
- **Math**: hendrycks/math, competition_math
- **Science**: allenai/scifact, scientific_papers
- **General**: OpenAssistant/oasst1, tatsu-lab/alpaca

### Government & Institutional Open Data

**NIH (National Institutes of Health)**
- **URL**: nih.gov
- **License**: Public domain (US government)
- **Content**: Medical and health research

**NASA**
- **URL**: nasa.gov
- **License**: Public domain (most content)
- **Content**: Space, astronomy, earth sciences
- **API**: Multiple APIs available

**NIST (National Institute of Standards and Technology)**
- **URL**: nist.gov
- **License**: Public domain
- **Content**: Standards, measurements, technical data

**UK Government Open Data**
- **URL**: data.gov.uk
- **License**: Open Government License
- **Content**: Various government datasets

**EU Open Data Portal**
- **URL**: data.europa.eu
- **License**: Various open licenses
- **Content**: European institutional data

### Specialized Research Databases

**Semantic Scholar**
- **URL**: semanticscholar.org
- **License**: Metadata freely available
- **API**: Comprehensive API for paper search and metadata
- **Purpose**: Find related papers, citations, influential works

**Google Scholar**
- **Note**: No official API, but can be scraped respectfully
- **Purpose**: Broad academic search

**CORE (COnnecting REpositories)**
- **URL**: core.ac.uk
- **License**: Aggregates open access papers
- **API**: Available
- **Content**: 200M+ open access papers

**BASE (Bielefeld Academic Search Engine)**
- **URL**: base-search.net
- **License**: Aggregates open access
- **Content**: Academic web resources

**DOAJ (Directory of Open Access Journals)**
- **URL**: doaj.org
- **License**: Lists journals with various CC licenses
- **API**: Available
- **Purpose**: Identify high-quality OA journals

### Code & Programming Resources

**GitHub**
- **License**: Varies (filter by license)
- **API**: GitHub API
- **MCP Server**: Available
- **Use**: Code examples, documentation, README files

**Stack Overflow**
- **License**: CC-BY-SA
- **API**: Stack Exchange API
- **Content**: Q&A for programming
- **Data Dumps**: Available quarterly

**Read the Docs**
- **License**: Varies
- **Content**: Software documentation
- **Purpose**: Programming tutorials and references

**PyPI / npm / crates.io**
- **Purpose**: Package documentation
- **License**: Varies
- **Use**: Programming examples, API references

### Data Science & ML Resources

**Kaggle Datasets**
- **URL**: kaggle.com/datasets
- **License**: Filter by license
- **Content**: Curated datasets for ML

**UCI Machine Learning Repository**
- **URL**: archive.ics.uci.edu/ml
- **License**: Various
- **Content**: Classic ML datasets

**Papers with Code**
- **URL**: paperswithcode.com
- **License**: Links to papers and code
- **Purpose**: Implementation examples, benchmarks

### Implementation Strategy

**Priority 1: Essential MCP Servers**
1. **arXiv MCP Server**: Primary academic source
2. **Wikipedia MCP Server**: General knowledge
3. **HuggingFace MCP Server**: Dataset integration
4. **GitHub MCP Server**: Code examples
5. **Semantic Scholar MCP**: Citation tracking

**Priority 2: Domain-Specific**
6. **bioRxiv/medRxiv MCP**: Life sciences
7. **chemRxiv MCP**: Chemistry
8. **PubMed Central MCP**: Biomedical literature
9. **Stack Overflow MCP**: Programming Q&A

**Priority 3: Specialized**
10. **OpenStax Tool**: Educational content
11. **PLOS Tool**: Open access journals
12. **NASA API Tool**: Space/earth sciences

**License Verification Workflow**:
```python
def verify_license(source_url, content):
    """
    Detect and verify license for content.
    
    Returns:
        {
            "license": "CC-BY-4.0",
            "license_url": "https://...",
            "is_permissive": True,
            "attribution_required": True,
            "commercial_use_allowed": True
        }
    """
    # Check common license patterns
    # Extract license from metadata
    # Verify against known permissive licenses
    # Flag for manual review if unclear
```

**Permissive License Priority**:
1. **CC0 (Public Domain)**: Maximum freedom
2. **CC-BY 4.0**: Attribution only
3. **CC-BY-SA 4.0**: Attribution + share-alike
4. **MIT / Apache-2.0**: For code
5. **CC-BY-NC**: Non-commercial (use cautiously)

**Integration Points**:
- Research Agent uses MCP servers for content retrieval
- License Compliance Checker validates sources
- HuggingFace integration for dataset augmentation and hosting
- Database stores license metadata for all sources

### 4. Specialist Capabilities
For complex domain tasks, the system uses specialist tools and agents:

**Code & Programming**:
- **Code Executor**: Runs and validates code snippets across multiple languages
- **Code Debugger**: Identifies and fixes errors in code
- **Bad Code Generator**: Creates intentionally buggy code for debugging training datasets
- **Code Optimizer**: Suggests performance improvements and refactoring
- **Test Generator**: Creates unit tests for code snippets
- **API Integration Tester**: Validates API calls and responses

**Mathematics & Calculations**:
- **Math Verifier**: Validates calculations, proofs, and mathematical reasoning
- **Equation Solver**: Solves algebraic, calculus, and differential equations
- **Statistical Analyzer**: Performs statistical calculations and hypothesis testing
- **Proof Checker**: Validates mathematical proofs step-by-step
- **LaTeX Formatter**: Formats mathematical expressions properly

**Chemistry & Sciences**:
- **Chemistry Simulator**: Balances equations, predicts reactions, calculates stoichiometry
- **Molecule Visualizer**: Generates molecular structures and properties
- **Physics Calculator**: Handles kinematics, dynamics, thermodynamics problems
- **Unit Converter**: Converts between different unit systems accurately

**Data & Analysis**:
- **Data Validator**: Checks data consistency, completeness, and accuracy
- **SQL Query Generator**: Creates and validates database queries
- **Data Visualization**: Generates charts, graphs, and visual representations
- **Statistical Model Checker**: Validates statistical models and assumptions

**Language & Text**:
- **Grammar Checker**: Validates grammar, spelling, and style
- **Citation Manager**: Formats references and citations correctly
- **Language Translator**: Handles multi-language content (for non-English datasets)
- **Text Summarizer**: Creates concise summaries of long content
- **Plagiarism Checker**: Ensures generated content is original

**Domain-Specific Experts**:
- **Medical Fact Checker**: Validates medical and health information
- **Legal Document Analyzer**: Reviews legal reasoning and terminology
- **Financial Calculator**: Handles financial models, valuations, and calculations
- **Historical Fact Verifier**: Cross-references historical claims
- **Scientific Literature Reviewer**: Checks against peer-reviewed sources

**Quality & Compliance**:
- **Bias Detector**: Identifies potential biases in generated content
- **Fact Checker**: Independently verifies factual claims via web search
- **Format Validator**: Ensures output matches training type requirements
- **Toxicity Filter**: Screens for harmful or inappropriate content
- **License Compliance Checker**: Validates proper attribution and licensing

**Advanced Reasoning**:
- **Multi-Step Reasoner**: Handles complex reasoning chains requiring multiple steps
- **Counterfactual Generator**: Creates alternative scenarios and outcomes
- **Contradiction Detector**: Identifies logical inconsistencies
- **Analogy Creator**: Generates explanatory analogies and metaphors
- **Socratic Questioner**: Creates follow-up questions for deeper understanding

## What Success Looks Like

### Minimal Viable Product (MVP)
A user can:
1. Request "Generate 10 SFT examples about organic chemistry"
2. The system autonomously generates all examples
3. Examples are factually accurate, well-formatted, and production-ready
4. Data is stored in the correct database table with quality scores
5. User can export data for immediate use in training

### Full Vision
- Support all 9 training types seamlessly
- Generate thousands of examples per request
- Maintain 90%+ quality approval rate
- Handle multi-modal data (text, code, equations)
- Provide analytics and quality dashboards
- Export to standard formats (JSONL, HuggingFace datasets)

## Technical Stack

### Framework
- **Google ADK (Agent Development Kit)**: Core agent orchestration
- **Gemini Models** (strategic selection based on task complexity):
  - **gemini-3-pro-preview**: Complex reasoning, planning, delegation (Orchestrator, Planning Agent, Generation Agent for complex domains)
  - **gemini-2.5-flash**: Simpler tasks, research, web search, data extraction (Research Agent, Question Agent, Database Agent)
  - **gemini-2.0-flash**: Fast operations, validation, formatting (Reviewer Agent for basic checks)

### Database
- **SQLAlchemy ORM**: Database abstraction
- **SQLite** (dev) / **PostgreSQL** (production)
- Schema supports all 9 training types

### Tools & Libraries
- **requests** + **BeautifulSoup4**: Web scraping
- **Pydantic**: Data validation
- **Code Executors**: Built-in (simple), AgentEngine (sandboxed), GKE (production)
- **MCP Servers**: arXiv, Wikipedia, HuggingFace, GitHub, Semantic Scholar, bioRxiv/medRxiv, chemRxiv
- **HuggingFace Hub**: Dataset repository for augmentation and hosting
- **datasets library**: Loading and processing HuggingFace datasets

## Current Implementation Status

### What's Built
- ✅ Complete database schemas for all training types
- ✅ Configuration system (YAML-based)
- ✅ Database tools (CRUD operations)
- ✅ Web tools (search, fetch, extract)
- ✅ Planning Agent (configured)
- ✅ Question Agent (configured)
- ✅ Research Agent (partially implemented)
- ✅ Basic orchestrator structure

### What's Missing (CRITICAL)
- ❌ **Generation Agent** - The core component that creates training data
- ❌ **Complete Research Agent** - Needs context storage implementation
- ❌ **Complete Reviewer Agent** - Only skeleton exists
- ❌ **Questions table updates** - Missing context fields
- ❌ **End-to-end workflow** - No integrated pipeline yet
- ❌ **Testing suite** - No tests written

### Priority Order
1. **Update Questions table** with context fields (ground_truth_context, synthesized_context)
2. **Complete Research Agent** to store both raw and synthesized context
3. **Build Generation Agent** - THIS IS THE MOST CRITICAL MISSING PIECE
4. **Complete Reviewer Agent** for quality validation
5. **Wire everything together** in main workflow
6. **Add testing** to ensure reliability

## How the System Works (Complete Flow)

### User Request
```
User: "Generate 100 GRPO examples for chemistry reasoning problems"
```

### Step-by-Step Process

**1. Orchestrator Receives Request**
- Asks clarifying questions if needed
- Routes to Planning Agent

**2. Planning Agent Creates Strategy**
```
Output: {
  topic: "chemistry",
  sub_topic: "stoichiometry, reaction mechanisms",
  training_type: "grpo",
  research_plan: "Focus on quantitative problems requiring multi-step reasoning",
  execution_plan: "Generate questions → Research → Create reasoning chains → Verify with code"
}
```

**3. Question Agent Generates Questions**
```
Output: {
  topic: "chemistry",
  sub_topic: "stoichiometry",
  questions: [
    "How many moles of CO2 are produced from 5.0g of C3H8?",
    "What is the limiting reagent in 2H2 + O2 → 2H2O with 4g H2 and 32g O2?",
    ... 100 questions total
  ]
}
→ Stored in questions table with status='pending', topic, and sub_topic fields populated
```

**4. Research Agent Gathers Context**
For each question:
- Searches authoritative sources (textbooks, journals, educational sites)
- Extracts **ground truth context** (word-for-word raw text from sources)
- Captures **source metadata** (URL, title, author, date)
- Identifies **potential license** (CC-BY, CC-BY-SA, public domain, copyright, etc.)
- Uses LLM to create **synthesized context** (clean, structured version)
```
Output stored in DB:
{
  question_id: 123,
  ground_truth_context: "Stoichiometry is the calculation of reactants and products...",
  synthesized_context: {
    "definition": "...",
    "formulas": ["n = m/M", "..."],
    "examples": [...]
  },
  context_sources: [
    {
      "url": "...", 
      "title": "...",
      "author": "...",
      "date_accessed": "2025-01-15",
      "license": "CC-BY-4.0",
      "license_url": "https://creativecommons.org/licenses/by/4.0/"
    }
  ],
  status: "researched"
}
```

**5. Generation Agent Creates Training Data**
For GRPO, generates:
- **Prompt**: The question
- **Reasoning**: Step-by-step chain of thought
- **Code**: Python verification script
- **Predicted Answer**: Extracted solution
- **Is Correct**: Boolean from code execution

```python
Example output:
{
  "prompt": "How many moles of CO2 are produced from 5.0g of C3H8?",
  "reasoning": """
  Step 1: Write balanced equation: C3H8 + 5O2 → 3CO2 + 4H2O
  Step 2: Calculate moles of C3H8: n = m/M = 5.0g / 44.1g/mol = 0.113 mol
  Step 3: Use stoichiometry: 1 mol C3H8 produces 3 mol CO2
  Step 4: Therefore: 0.113 mol × 3 = 0.340 mol CO2
  """,
  "code": """
  molar_mass_C3H8 = 44.1  # g/mol
  mass_C3H8 = 5.0  # g
  moles_C3H8 = mass_C3H8 / molar_mass_C3H8
  moles_CO2 = moles_C3H8 * 3  # stoichiometric ratio
  print(f"Answer: {moles_CO2:.3f} mol CO2")
  """,
  "predicted_answer": "0.340 mol CO2",
  "is_correct": True
}
→ Stored in synthetic_data_grpo table
```

**6. Reviewer Agent Validates**
- Checks reasoning logic
- Executes code to verify answer
- Fact-checks with independent web search
- Assigns quality score (0-1)
- Updates review_status: "approved", "needs_revision", or "rejected"

**7. Final Output**
- 100 high-quality GRPO examples ready for training
- Stored in database with quality scores
- Can be exported to JSONL or other formats

## Special Considerations

### Context is King
The **Research Agent** is crucial because it provides the factual foundation for all generated data. It stores TWO versions of context:

1. **Ground Truth** (raw): Word-for-word text from authoritative sources
   - Preserves exact terminology and details
   - Maintains citations and sources
   - **Tracks licenses** (CC-BY, CC-BY-SA, public domain, copyright, etc.)
   - Records source metadata (URL, title, author, date accessed)
   
2. **Synthesized** (cleaned): LLM-structured version
   - Organized into definitions, concepts, examples
   - Easier for Generation Agent to work with
   - Still factually accurate
   - Derived from properly licensed ground truth

**License Compliance**: All source material must have license information tracked. This ensures:
- Legal compliance for generated datasets
- Proper attribution when required
- Transparency about data provenance
- Ability to filter by license type (e.g., only use CC-BY sources)

### Code Must Work
For programming and STEM datasets:
- All code must execute successfully
- Results must be verified
- Bad code (for debugging datasets) must fail predictably
- Use sandboxed code executors for safety

### Quality Thresholds
- Target: 90%+ approval rate
- Auto-reject: quality_score < 0.6
- Flag for review: 0.6 ≤ quality_score < 0.8
- Auto-approve: quality_score ≥ 0.8

## What This Is NOT

### Not a Data Augmentation Tool
This doesn't paraphrase or slightly modify existing data. It creates genuinely new examples from scratch based on research.

### Not a Scraper
While it uses web scraping for research, the goal is to create **new synthetic data**, not to collect existing datasets.

### Not a Single-Agent System
This is explicitly a **multi-agent orchestration** where specialized agents collaborate. Each agent has a distinct role.

### Not Limited to One Domain
While chemistry is a focus area (given the creator's background), the system must support mathematics, programming, and other STEM fields equally well.

## Success Metrics

### Quantitative
- Generate 1000+ examples per hour (once optimized)
- 90%+ quality approval rate
- <5% factual error rate
- Support all 9 training types

### Qualitative
- Data is indistinguishable from human-created examples
- Sufficient for actual LLM training use
- Covers diverse sub-topics within each domain
- Includes appropriate difficulty range (easy → hard)

## Developer Context

### Creator Background
- Chemist by training
- Strong Python skills
- Learning: TypeScript, React, Rust, C#, C++
- Aspires to work as: AI Engineer, Data Scientist, or Full Stack Software Engineer
- British (prefers understated communication, no excessive enthusiasm)

### Development Philosophy
- Code-first approach
- Modular, extensible architecture
- Production-quality from the start
- Comprehensive testing
- Clear documentation

## Critical Path to MVP

The absolute minimum to get a working system:

1. ✅ Database schema (DONE)
2. 🔧 Update Questions table with context fields
3. 🔧 Complete Research Agent context storage
4. ❌ **BUILD GENERATION AGENT** ← THIS IS THE BLOCKER
5. 🔧 Complete Reviewer Agent
6. 🔧 Wire workflow together
7. 🔧 Test end-to-end with SFT (simplest training type)

Once SFT works end-to-end, expand to other training types.

## Long-Term Vision

### Phase 1 (MVP): Single Training Type
- SFT data generation working end-to-end
- Manual quality review
- 100 examples per run

### Phase 2: Multiple Training Types
- Support SFT, DPO, GRPO
- Automated quality review
- 1000+ examples per run

### Phase 3: Production System
- All 9 training types
- Parallel processing
- Quality dashboards
- Export to standard formats
- Human-in-the-loop review UI

### Phase 4: Advanced Features
- Multi-modal data (images, audio)
- Adversarial example generation
- Active learning (identify gaps)
- Data augmentation
- Version control and lineage tracking

## Key Constraints

### Must Haves
- Factual accuracy (non-negotiable)
- Code that actually works
- Proper citations/sources
- Quality scoring on every example
- Support for all defined training types

### Nice to Haves
- Beautiful UI
- Real-time progress tracking
- Deployment to cloud
- API endpoints
- Integration with training pipelines

### Technical Constraints
- Use Google ADK (not LangChain or other frameworks)
- Use Gemini models (gemini-3-pro-preview, gemini-2.5-flash, gemini-2.0-flash based on task complexity)
- SQLAlchemy for database
- Store everything in structured databases (not flat files)
- Capture source licenses for all research content
- Integrate MCP servers for external data access (arXiv, Wikipedia, HuggingFace, etc.)
- Prioritize permissive licenses (CC-BY, CC0, MIT, Apache-2.0)

## Summary

This is an **autonomous synthetic data generation factory** for LLM training. It takes high-level requests from users and produces production-ready training datasets through a multi-stage process of planning, research, generation, and review. The system prioritizes quality and factual accuracy above all else, using a sophisticated multi-agent architecture built on Google ADK.

The **Generation Agent** is the critical missing piece that bridges research and final output. Once built, it will enable the complete workflow and make the system functional.

## Usage Example

**Input**: "Generate 50 DPO examples for organic chemistry reactions"

**Output**: Database table `synthetic_data_dpo` containing:
```
50 rows of:
- prompt: "What is the mechanism of SN2 reaction?"
- chosen: [detailed, accurate, well-structured response]
- rejected: [less helpful or partially incorrect response]
- chosen_rating: 5.0
- rejected_rating: 2.5
- quality_score: 0.92
- review_status: "approved"
- sources: [list of research URLs]
```

Ready to export and use for DPO training.