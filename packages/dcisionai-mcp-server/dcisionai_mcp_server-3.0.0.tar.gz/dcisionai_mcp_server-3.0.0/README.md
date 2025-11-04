# 🎯 DcisionAI MCP Server

**AI-Powered Optimization for Your IDE** - Solve complex business problems directly in Cursor, Claude Desktop, or VS Code.

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://pypi.org/project/dcisionai-mcp-server/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## ✨ What is This?

DcisionAI is a **Model Context Protocol (MCP) server** that brings enterprise-grade optimization to your IDE. Ask your AI assistant to solve real business problems, and get:

- 🎯 **90%+ Trust Scores** with mathematical proof
- 🧠 **DAME Algorithm** (proprietary evolutionary solver)
- ⚖️ **Dual Validation** with HiGHS exact solver
- 💼 **Business Interpretation** in plain language
- 📊 **5-Layer Proof Suite** for transparency

---

## 🚀 Quick Start (30 seconds)

### **Step 1: Install in Your IDE**

**For Cursor / Claude Desktop:**

Add to your MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "dcisionai": {
      "command": "uvx",
      "args": ["dcisionai-mcp-server@latest"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your-anon-key"
      },
      "autoApprove": ["dcisionai_solve"]
    }
  }
}
```

**That's it!** No compilation, no setup, no auth tokens.

---

### **Step 2: Try It**

Ask Claude/Cursor:

```
"Use DcisionAI to optimize my retail store layout: 
20 products across 5 shelves, maximize revenue and customer flow."
```

Get back:
- ✅ Optimal product placement
- ✅ 90% trust score with mathematical proof
- ✅ Business interpretation
- ✅ Constraint verification
- ✅ Sensitivity analysis

---

## 🎓 What Can It Solve?

### **📊 Finance**
- **Portfolio Optimization** - Rebalance $500k portfolio, reduce concentration risk
- **Trading Schedule** - Optimize execution timing to minimize market impact
- **Asset Allocation** - Balance risk/return across sectors

### **🏪 Retail**
- **Store Layout** - Optimize shelf space for 20+ products
- **Promotion Scheduling** - Maximize revenue with budget constraints
- **Inventory Placement** - Minimize stockouts & overstock

### **🚚 Logistics**
- **Vehicle Routing** - Minimize travel time for 10+ delivery stops
- **Warehouse Layout** - Optimize picking paths
- **Job Shop Scheduling** - Sequence 15 jobs across 5 machines

### **👷 Workforce**
- **Shift Scheduling** - Assign 20 workers to 40 shifts
- **Maintenance Scheduling** - Minimize downtime across 10 assets
- **Skill Matching** - Optimal worker-task assignment

---

## 🔧 Environment Variables

Required in your IDE's MCP config:

```bash
# LLM APIs (required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Supabase (required - stores domain configs)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ...

# Optional: External data (for real-world augmentation)
POLYGON_API_KEY=...              # Market data
ALPHA_VANTAGE_API_KEY=...        # Economic data
```

---

## 📊 Trust & Validation

Every solution includes:

### **1. Mathematical Proof Suite (5 proofs)**
- **Constraint Verification** - All business rules satisfied?
- **Monte Carlo Simulation** - 1000 scenarios, how stable?
- **Optimality Certificate** - How close to theoretical best?
- **Sensitivity Analysis** - What if inputs change ±20%?
- **Benchmark Comparison** - Beats naive baseline by X%?

### **2. Dual Solver Validation**
- **DAME** (heuristic) - Fast, handles any problem
- **HiGHS** (exact) - Slow, LP/MIP only, mathematically optimal
- **Cross-validation** - Compare results, boost trust to 95%+

### **3. Business Interpretation**
- Plain language explanation
- Implementation steps
- Risks & assumptions
- What-if scenarios

---

## 💡 Example Interaction

**You ask:**
```
"I have 50 products to place on 8 store shelves. 
Products have different profit margins and sales rates. 
Dairy needs refrigeration. High-value items need security.
How should I arrange them?"
```

**DcisionAI returns:**
```
✅ Status: SUCCESS
📊 Industry: RETAIL
🎯 Domain: Store Layout Optimization
⭐ Trust Score: 92% (VERIFIED)
🏆 Certification: VERIFIED

📈 Objective Value: 0.423 (42.3% improvement vs. baseline)

💼 Business Interpretation:
"Strategic product placement optimizes for revenue and customer 
flow. High-margin products positioned in prime visibility zones. 
Refrigerated items grouped for efficiency..."

🔍 Mathematical Proof:
✅ All 8 constraints satisfied
✅ Monte Carlo: 1000 scenarios, 95% confidence
✅ Optimality: Within 4.2% of theoretical best
✅ Sensitivity: Stable under ±20% demand changes
✅ Benchmark: 42% better than random placement

🛠️ Implementation Steps:
1. Reorganize shelf 1-3 (high-traffic zone)
2. Group dairy in refrigerated section
3. Position security items near checkout
4. Monitor sales for 30 days and adjust
```

---

## 🏗️ Architecture

```
User Question
    ↓
LLM Extraction (GPT-4/Claude)
    ↓
Domain Classification (11 domains)
    ↓
Data Augmentation (synthetic + external APIs)
    ↓
Parallel Solving
    ├─ DAME (heuristic, 100 generations)
    └─ HiGHS (exact, LP/MIP)
    ↓
Cross-Validation
    ↓
Proof Generation (5 proofs)
    ↓
Business Interpretation (LLM)
    ↓
Structured Response (JSON)
```

---

## 📚 Supported Domains

| Domain | Description | Example |
|--------|-------------|---------|
| **Portfolio** | Asset allocation, risk balancing | "Optimize $500k portfolio" |
| **Retail Layout** | Shelf space allocation | "Place 20 products on 5 shelves" |
| **VRP** | Vehicle routing, delivery optimization | "Route 3 trucks to 15 stops" |
| **Job Shop** | Production scheduling | "Schedule 10 jobs on 4 machines" |
| **Workforce** | Shift assignment, rostering | "Assign 15 workers to 40 shifts" |
| **Maintenance** | Asset maintenance scheduling | "Schedule maintenance for 8 machines" |
| **Promotion** | Marketing campaign optimization | "Allocate $50k ad budget" |
| **Trading** | Trade execution optimization | "Minimize market impact of large order" |
| **Customer Onboarding** | Wealth management | "Onboard new client with $2M" |
| **PE Exit Timing** | Private equity exits | "Optimize exit timing for 5 holdings" |
| **HF Rebalancing** | Hedge fund portfolio adjustments | "Rebalance multi-strategy fund" |

---

## 🔬 Technology Stack

- **DAME** - Proprietary evolutionary algorithm (see [research paper](https://github.com/dcisionai/dcisionai-mcp-platform/blob/main/papers/DcisionAI.pdf))
- **HiGHS** - Open-source LP/MIP solver from Edinburgh
- **FastMCP** - Model Context Protocol implementation
- **Anthropic Claude** - LLM for extraction & interpretation
- **OpenAI GPT-4** - Fallback LLM
- **Supabase** - Domain config storage

---

## 📖 Documentation

- **Research Paper**: [DcisionAI.pdf](https://github.com/dcisionai/dcisionai-mcp-platform/blob/main/papers/DcisionAI.pdf)
- **GitHub**: [dcisionai/dcisionai-mcp-platform](https://github.com/dcisionai/dcisionai-mcp-platform)
- **Issues**: [Report a bug](https://github.com/dcisionai/dcisionai-mcp-platform/issues)

---

## 🛠️ Development

### **Local Testing**

```bash
# Clone the repo
git clone https://github.com/dcisionai/dcisionai-mcp-platform.git
cd dcisionai-mcp-platform/dcisionai/fastapi-server

# Install dependencies
pip install -e .

# Run locally
python -m dcisionai_mcp_server.server
```

### **Contributing**

We welcome contributions! See [CONTRIBUTING.md](https://github.com/dcisionai/dcisionai-mcp-platform/blob/main/CONTRIBUTING.md).

---

## 📜 License

MIT License - see [LICENSE](https://github.com/dcisionai/dcisionai-mcp-platform/blob/main/LICENSE)

---

## 🤝 Support

- **Email**: amey@dcisionai.com
- **GitHub Issues**: [Report a bug](https://github.com/dcisionai/dcisionai-mcp-platform/issues)
- **Docs**: [Full documentation](https://github.com/dcisionai/dcisionai-mcp-platform)

---

## 🎉 Credits

Built by [Amey Dhavle](https://github.com/ameydhavle)

Powered by:
- FastMCP
- HiGHS Solver
- Anthropic Claude
- OpenAI GPT-4
- Supabase

---

**⭐ Star us on GitHub if DcisionAI helps your business!**

[github.com/dcisionai/dcisionai-mcp-platform](https://github.com/dcisionai/dcisionai-mcp-platform)
