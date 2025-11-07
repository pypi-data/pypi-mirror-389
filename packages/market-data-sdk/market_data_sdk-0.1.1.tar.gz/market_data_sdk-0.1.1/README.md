# Epoch Data Research Tools

A unified SDK for accessing Polygon.io and TradingEconomics market data with LangGraph integration.

**[📚 Documentation](docs/README.md)** | **[🏗️ Architecture](docs/EPOCH_ASSET_ARCHITECTURE.md)** | **[✅ Tests (31/31)](docs/TEST_RESULTS.md)** | **[🤝 Contributing](CONTRIBUTING.md)** | **[📊 Status](PROJECT_STATUS.md)**

---

## ✨ Key Features

### Universal Asset Layer
```python
from common.models.asset import EpochAsset, AssetType

# Provider-agnostic representation
asset = EpochAsset(symbol="BTC-USD", asset_type=AssetType.CRYPTO)
asset.to_epoch_asset_id()  # → "^BTCUSD-Crypto"
```

### Polygon Integration
```python
from epoch_polygon.registry import get_tools

# Get 8 LangGraph tools
tools = get_tools()

# Use with agent
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(llm, tools)
```

### Generic Execution
Single `_execute()` method handles **ALL** Polygon endpoints:
- ✅ Stocks, Crypto, Forex, Options, Indices, Futures
- ✅ Type-based detection (no field name assumptions)
- ✅ market_type injection, pair splitting, date filters

---

## 🚀 Quick Start

### 1. Installation
```bash
# Clone repository
git clone <repo-url>
cd EpochDataResearchTools

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package
pip install -e ".[dev]"
```

### 2. Set up API keys
```bash
cp .env.example .env
# Edit .env and add:
# POLYGON_API_KEY=your_key_here
```

### 3. Run tests
```bash
pytest  # 31/31 tests passing ✅
```

### 4. Try examples
```bash
python examples/polygon/basic_aggregates.py
```

---

## 📦 Package Structure

```
EpochDataResearchTools/
├── src/
│   ├── common/              # Universal models (EpochAsset)
│   ├── epoch_polygon/       # Polygon adapter
│   └── tradingeconomics/    # TradingEconomics adapter
│
├── tests/                   # 31 passing tests
│   ├── common/              # 13 EpochAsset tests
│   └── polygon/             # 18 Polygon tests
│
├── examples/                # Ready-to-run examples
├── docs/                    # Comprehensive documentation
└── [config files]
```

---

## 🎯 Usage Examples

### Basic: Get Stock Data
```python
from common.models.asset import EpochAsset, AssetType
from epoch_polygon.models.asset import PolygonAsset
from epoch_polygon.models.requests import AggregatesRequest
from epoch_polygon.models.filters import DateFilter
from epoch_polygon.registry import get_tools

# 1. Create universal asset
epoch_asset = EpochAsset(symbol="AAPL", asset_type=AssetType.STOCK)

# 2. Convert to Polygon format
polygon_asset = PolygonAsset.from_epoch_asset(epoch_asset)

# 3. Create request
request = AggregatesRequest(
    asset=polygon_asset,
    date_filter=DateFilter.last_n_days(30),
    timespan="day",
    multiplier=1
)

# 4. Use with tools
tools = get_tools()
# tools[0].invoke(request.model_dump())
```

### Advanced: LangGraph Agent
```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from epoch_polygon.registry import get_tools

# Create agent with Polygon tools
llm = ChatOpenAI(model="gpt-4")
tools = get_tools()
agent = create_react_agent(llm, tools)

# Ask questions
result = agent.invoke({
    "messages": [("user", "What was AAPL's closing price yesterday?")]
})
```

---

## 🏗️ Architecture

### EpochAsset Flow
```
Agent → EpochAsset → PolygonAsset.from_epoch_asset() → Polygon API
                  → TEAsset.from_epoch_asset() → TE API
```

### Asset Conventions
- **Stocks**: `AAPL`, `TSLA` → `"AAPL-Stock"`
- **Crypto**: `BTC-USD`, `BTC` (defaults to USD) → `"^BTCUSD-Crypto"`
- **Forex**: `EUR-USD` → `"^EURUSD-Forex"`
- **Futures**: `ES` → `"ES-Future"`
- **Indices**: `SPX` → `"^SPX-Index"`

See [EPOCH_ASSET_ARCHITECTURE.md](docs/EPOCH_ASSET_ARCHITECTURE.md) for details.

---

## ✅ Testing

```bash
# All tests
pytest

# Specific suite
pytest tests/common/     # EpochAsset tests
pytest tests/polygon/    # Polygon tests

# With coverage
pytest --cov=src --cov-report=html

# Verbose
pytest -v
```

**Current Status**: 31/31 tests passing (0.88s)

See [TEST_RESULTS.md](docs/TEST_RESULTS.md) for details.

---

## 📚 Documentation

- **[Documentation Index](docs/README.md)** - Start here
- **[Architecture Guide](docs/EPOCH_ASSET_ARCHITECTURE.md)** - Universal asset layer
- **[Package Structure](docs/PACKAGE_STRUCTURE.md)** - Code organization
- **[Test Results](docs/TEST_RESULTS.md)** - Coverage details
- **[Summary](docs/SUMMARY.md)** - Implementation overview
- **[Contributing](CONTRIBUTING.md)** - Development guidelines
- **[Project Status](PROJECT_STATUS.md)** - Current state & roadmap

---

## 🛣️ Roadmap

### Completed ✅
- Universal asset layer (EpochAsset)
- Polygon integration (4 clients, 8 tools)
- Generic `_execute()` for all endpoints
- Comprehensive test suite (31 tests)
- Organized documentation

### In Progress 🚧
- TradingEconomics integration

### Planned 📋
- More Polygon endpoints (indicators, financials, reference)
- `from_epoch_asset_id()` parser
- Real-world integration tests
- Performance benchmarks

See [TODO.md](docs/TODO.md) for detailed roadmap.

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code standards
- Architecture patterns
- Testing guidelines
- PR process

---

## 📄 License

MIT License

---

## 🔗 Links

- [Polygon.io API](https://polygon.io) - Stock market data
- [TradingEconomics](https://tradingeconomics.com) - Economic data
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent framework
