# Writing Assistant AI MCP Server
**By MEOK AI Labs** | [meok.ai](https://meok.ai)

Content writing toolkit: headline generation, readability scoring, tone analysis, outline building, and plagiarism similarity checking.

## Tools

| Tool | Description |
|------|-------------|
| `generate_headlines` | Generate headline variations with SEO and power word analysis |
| `score_readability` | Flesch, Gunning Fog, Coleman-Liau readability metrics |
| `analyze_tone` | Detect formal, casual, academic, persuasive, technical tone |
| `build_outline` | Structured content outline with word allocations and SEO tips |
| `check_similarity` | Jaccard, cosine, and trigram plagiarism similarity check |

## Installation

```bash
pip install mcp
```

## Usage

### Run the server

```bash
python server.py
```

### Claude Desktop config

```json
{
  "mcpServers": {
    "writing-assistant": {
      "command": "python",
      "args": ["/path/to/writing-assistant-ai-mcp/server.py"]
    }
  }
}
```

## Pricing

| Tier | Limit | Price |
|------|-------|-------|
| Free | 30 calls/day | $0 |
| Pro | Unlimited + premium features | $9/mo |
| Enterprise | Custom + SLA + support | Contact us |

## License

MIT
