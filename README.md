# AWS Bedrock RAG System for Intelligent Document Querying

A production-ready Retrieval-Augmented Generation (RAG) system built with Amazon Bedrock, Aurora PostgreSQL with pgvector, and Streamlit. This application provides intelligent question-answering capabilities for heavy machinery documentation using Claude 3 AI models with source attribution.

## 🎯 Project Overview

This system demonstrates a complete RAG implementation that:

- **Validates prompts** to ensure queries are relevant to heavy machinery
- **Retrieves contextual information** from a vector database using semantic search
- **Generates accurate responses** using Claude 3 AI models
- **Displays source attribution** showing which documents were used for each answer
- **Maintains conversation history** in an interactive chat interface

### Key Features

✅ **Prompt Validation**: Categorizes and filters user queries to ensure relevance  
✅ **Vector Search**: Uses Amazon Titan embeddings (1536 dimensions) for semantic similarity  
✅ **RAG Pipeline**: Combines retrieved context with LLM generation for accurate answers  
✅ **Source Attribution**: Shows document sources, S3 locations, and relevance scores  
✅ **Configurable Parameters**: Adjustable temperature and top_p for response control  
✅ **Multi-Model Support**: Works with Claude 3 Haiku and Sonnet models  
✅ **Production Infrastructure**: Full Terraform deployment with VPC, Aurora, and S3

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit UI (app.py)                 │
│                  Chat Interface + Controls               │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   bedrock_utils.py                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │valid_prompt()│  │query_kb()    │  │generate_     │  │
│  │              │  │              │  │response()    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────┬─────────────────┬────────────────┬──────────┘
           │                 │                │
           ▼                 ▼                ▼
    ┌──────────┐    ┌──────────────┐   ┌─────────────┐
    │ Bedrock  │    │   Bedrock    │   │   Aurora    │
    │ Claude 3 │    │ Knowledge    │   │ PostgreSQL  │
    │          │    │ Base         │   │ + pgvector  │
    │          │    │              │   │ + indexes   │
    └──────────┘    └──────┬───────┘   └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  S3 Bucket   │
                    │    (PDFs)    │
                    └──────────────┘
```

## 📋 Prerequisites

- **AWS Account** with appropriate permissions
- **AWS CLI** configured with credentials
- **Terraform** >= 1.0
- **Python** 3.9+
- **Access to Amazon Bedrock** models (Claude 3, Titan Embeddings)
- **Git** for version control

## 🚀 Quick Start

### 1. Clone the Repository

\`\`\`bash
git clone <repository-url>
cd cd13926-Building-Generative-AI-Applications-with-Amazon-Bedrock-and-Python-project-solution
\`\`\`

### 2. Deploy Infrastructure (Stack 1)

Deploy VPC, Aurora PostgreSQL, and S3 bucket:

\`\`\`bash
cd stack1
terraform init
terraform apply
\`\`\`

**Note the outputs:**

- \`aurora_endpoint\` - Database endpoint
- \`rds_secret_arn\` - Credentials secret
- \`s3_bucket_name\` - S3 bucket for documents

### 3. Configure Aurora Database

Connect to Aurora using RDS Query Editor in AWS Console and run each SQL statement:

\`\`\`sql
-- 1. Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create schema
CREATE SCHEMA IF NOT EXISTS bedrock_integration;

-- 3. Create user role
DO $$ BEGIN
CREATE ROLE bedrock_user LOGIN;
EXCEPTION WHEN duplicate_object THEN
RAISE NOTICE 'Role already exists';
END $$;

-- 4. Grant permissions
GRANT ALL ON SCHEMA bedrock_integration to bedrock_user;

-- 5. Create table with vector column
CREATE TABLE IF NOT EXISTS bedrock_integration.bedrock_kb (
id uuid PRIMARY KEY,
embedding vector(1536),
chunks text,
metadata json
);

-- 6. Create HNSW index for vector similarity search
CREATE INDEX IF NOT EXISTS bedrock_kb_embedding_idx
ON bedrock_integration.bedrock_kb
USING hnsw (embedding vector_cosine_ops);

-- 7. Create GIN index for text search (REQUIRED by Bedrock)
CREATE INDEX IF NOT EXISTS bedrock_kb_chunks_idx
ON bedrock_integration.bedrock_kb
USING gin (to_tsvector('english', chunks));
\`\`\`

### 4. Upload Documents to S3

\`\`\`bash
cd ../scripts
python3 upload_s3.py
\`\`\`

This uploads the heavy machinery specification PDFs to your S3 bucket.

### 5. Deploy Bedrock Knowledge Base (Stack 2)

\`\`\`bash
cd ../stack2
terraform init
terraform apply
\`\`\`

**Note the output:**

- \`bedrock_knowledge_base_id\` - Use this in the Streamlit app

### 6. Sync Knowledge Base

1. Go to AWS Console → Amazon Bedrock → Knowledge bases
2. Click on \`my-bedrock-kb\`
3. Go to **Data sources** tab
4. Click **Sync** button
5. Wait for sync to complete (~1-2 minutes)

### 7. Run the Application

\`\`\`bash
cd ..
python3 -m venv venv
source venv/bin/activate # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
\`\`\`

The app will open at \`http://localhost:8501\`

## 🎮 How to Use

### Configuration (Sidebar)

1. **Select LLM Model**: Choose between Claude 3 Haiku (faster, cheaper) or Sonnet (more capable)
2. **Knowledge Base ID**: Enter your KB ID from Stack 2 output
3. **Temperature** (0.0-1.0): Controls randomness
   - Low (0.0-0.3): Precise, factual responses
   - High (0.7-1.0): Creative, varied responses
4. **Top_P** (0.0-1.0): Controls diversity
   - Low: More focused responses
   - High: More diverse token selection

### Asking Questions

**Valid Questions (Heavy Machinery Topics):**

- "What is the payload capacity of the dump truck?"
- "Tell me about the hydraulic system of the excavator"
- "What are the safety features of the bulldozer?"
- "How does the forklift's lifting mechanism work?"

**Invalid Questions (Will be Rejected):**

- General knowledge questions
- Profanity or toxic content
- Questions about how the AI works
- Off-topic subjects

### Understanding Responses

Each response includes:

1. **AI-Generated Answer**: Comprehensive answer based on retrieved context
2. **📚 View Sources** (Expandable): Shows:
   - **Source Number** with relevance score (e.g., 87.5%)
   - **Document Name** (e.g., \`excavator-x950-spec-sheet.pdf\`)
   - **S3 Location** (full path)
   - **Content Preview** (first 200 characters)
   - **Metadata** (if available)

## 📁 Project Structure

```
.
├── app.py                      # Streamlit web application
├── bedrock_utils.py            # Core RAG functions
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── modules/                    # Terraform modules
│   ├── database/               # Aurora PostgreSQL module
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   └── bedrock_kb/             # Bedrock Knowledge Base module
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── stack1/                     # Infrastructure stack
│   ├── main.tf                 # VPC, Aurora, S3
│   ├── variables.tf
│   └── outputs.tf
│
├── stack2/                     # Bedrock stack
│   ├── main.tf                 # Knowledge Base
│   ├── variables.tf
│   └── outputs.tf
│
└── scripts/                    # Utility scripts
    ├── aurora_sql.sql          # Database setup SQL
    ├── upload_s3.py            # Upload PDFs to S3
    │
    └── spec-sheets/            # Heavy machinery PDFs
        ├── bulldozer-bd850-spec-sheet.pdf
        ├── dump-truck-dt1000-spec-sheet.pdf
        ├── excavator-x950-spec-sheet.pdf
        ├── forklift-fl250-spec-sheet.pdf
        └── mobile-crane-mc750-spec-sheet.pdf
```

## 🔧 Core Components

### 1. \`bedrock_utils.py\`

Three main functions:

#### \`valid_prompt(prompt, model_id)\`

Validates user prompts using Claude 3 to classify into categories:

- **Category A**: Questions about the AI system
- **Category B**: Toxic/profane content
- **Category C**: Off-topic questions
- **Category D**: Meta/instruction questions
- **Category E**: Heavy machinery questions ✅ (only valid category)

Returns \`True\` only for Category E.

#### \`query_knowledge_base(query, kb_id)\`

Retrieves relevant context from Bedrock Knowledge Base:

- Queries using semantic search
- Returns top 3 most relevant chunks
- Includes source metadata (S3 URI, relevance score)
- Structured output with content, score, and source info

#### \`generate_response(prompt, model_id, temperature, top_p)\`

Generates AI responses using Claude 3:

- Accepts full prompt with context
- Configurable temperature and top_p parameters
- Returns formatted text response
- Handles errors gracefully

### 2. \`app.py\`

Streamlit application with:

- **Chat interface** with message history
- **Sidebar configuration** for model settings
- **Prompt validation** before processing
- **Knowledge Base query** for context retrieval
- **Response generation** with source attribution
- **Session state management** for persistence

### 3. Terraform Infrastructure

**Stack 1** (Foundation):

- VPC with public/private subnets across 3 AZs
- Aurora Serverless v2 PostgreSQL 15.13
- S3 bucket with versioning and encryption
- Security groups and IAM roles
- Secrets Manager for database credentials

**Stack 2** (Bedrock):

- Bedrock Knowledge Base
- S3 data source configuration
- IAM roles for Bedrock access
- RDS vector database integration

## �� Troubleshooting

### Knowledge Base Returns 0 Results

- **Check**: Data source is synced (AWS Console → Bedrock → Knowledge Bases)
- **Check**: PDFs uploaded to S3
- **Check**: Aurora database has data

### Terraform Errors

- **"Cannot find version 15.4"**: Use Aurora PostgreSQL 15.13+
- **"Embedding model ARN region mismatch"**: Ensure region is \`us-east-1\`
- **"chunks column must be indexed"**: Run the GIN index SQL command

### Connection Errors

- **Check**: AWS credentials configured (\`aws configure\`)
- **Check**: Region matches (us-east-1)
- **Check**: IAM permissions for Bedrock, RDS, S3

## 📝 License

This project is part of the Udacity AWS AI & ML Scholarship Program.

---

**Built with ❤️ using Amazon Bedrock, Aurora PostgreSQL, and Streamlit**
