# Deep Agents - Tài liệu tìm hiểu

> **Nguồn:** [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) (bản sao tại `C:\Users\tungm\Desktop\deepagents`)
> **Phiên bản:** 0.6.10
> **License:** MIT

---

## 1. Tổng quan

**Deep Agents** là một open-source agent harness ("bộ khung agent có pin kèm theo") được xây dựng bởi LangChain. Nó cung cấp một agent coding trong terminal chạy ngay lập tức, có thể tùy chỉnh, mở rộng hoặc thay thế bất kỳ thành phần nào.

### 1.1 Vị trí trong hệ sinh thái LangChain

```
LangGraph (graph runtime)
  └── LangChain create_agent (minimal agent harness)
       └── Deep Agents (opinionated harness)
            ├── Filesystem (đọc/ghi/tìm kiếm file)
            ├── Sub-agents (ủy thác tác vụ)
            ├── Context management (tự động tóm tắt)
            ├── Skills (kỹ năng tải theo yêu cầu)
            ├── Memory (bộ nhớ xuyên phiên)
            └── Human-in-the-loop (phê duyệt tool calls)
```

### 1.2 Nguyên lý thiết kế

| Nguyên lý | Mô tả |
|-----------|-------|
| **Opinionated** | Mặc định được tinh chỉnh cho công việc đa bước, đường dài |
| **Extensible** | Có thể ghi đè hoặc thay thế bất kỳ thành phần nào |
| **Model-agnostic** | Hoạt động với mọi LLM hỗ trợ tool calling |
| **Production-ready** | Xây dựng trên LangGraph, tích hợp LangSmith |

---

## 2. Kiến trúc Monorepo

```
deepagents/
├── libs/
│   ├── deepagents/          # Core SDK (package: deepagents, v0.6.10)
│   │   └── deepagents/
│   │       ├── graph.py           # create_deep_agent() - entry point chính
│   │       ├── backends/          # Pluggable storage backends
│   │       ├── middleware/        # Middleware stack (11 middleware)
│   │       └── profiles/          # Harness & Provider profiles
│   ├── code/                # Deep Agents Code (Textual TUI)
│   ├── cli/                 # Deployment CLI (init/dev/deploy)
│   ├── acp/                 # Agent Context Protocol server
│   ├── evals/               # Evaluation suite + Harbor
│   ├── talon/               # Experimental long-running runtime
│   └── partners/            # 5 sandbox providers
├── examples/                # 18 example projects
└── .github/                 # CI/CD (40+ workflows)
```

### 2.1 Các packages chính

| Package | PyPI | Mô tả |
|---------|------|-------|
| `deepagents` | [deepagents](https://pypi.org/project/deepagents/) | Core SDK |
| `deepagents-code` | [deepagents-code](https://pypi.org/project/deepagents-code/) | Coding agent TUI |
| `deepagents-cli` | [deepagents-cli](https://pypi.org/project/deepagents-cli/) | Deploy CLI |
| `deepagents-acp` | [deepagents-acp](https://pypi.org/project/deepagents-acp/) | ACP server |
| `deepagents-evals` | [deepagents-evals](https://pypi.org/project/deepagents-evals/) | Evaluations |
| `deepagents-talon` | [deepagents-talon](https://pypi.org/project/deepagents-talon/) | Runtime host |

---

## 3. Core SDK

### 3.1 Entry Point: `create_deep_agent()`

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-5.5",
    tools=[my_custom_tool],
    system_prompt="You are a research assistant.",
)

result = agent.invoke({"messages": "Research LangGraph and write a summary"})
```

**Tham số chính:**
- `model` — `provider:model` string hoặc `BaseChatModel` instance
- `tools` — Tools bổ sung (additive với built-in tools)
- `system_prompt` — Custom instructions (luôn ở đầu prompt)
- `middleware` — Middleware bổ sung
- `subagents` — Sub-agent specs (SubAgent / CompiledSubAgent / AsyncSubAgent)
- `skills` — Danh sách skill source paths
- `memory` — AGENTS.md files để load vào system prompt
- `permissions` — Filesystem permission rules
- `backend` — Storage backend (default: StateBackend)
- `interrupt_on` — Human-in-the-loop config
- `response_format` — Structured output format

### 3.2 Built-in Tools

| Tool | Nguồn | Mô tả |
|------|-------|-------|
| `write_todos` | TodoListMiddleware | Quản lý danh sách việc cần làm |
| `ls` | FilesystemMiddleware | Liệt kê file/thư mục |
| `read_file` | FilesystemMiddleware | Đọc nội dung file |
| `write_file` | FilesystemMiddleware | Ghi file |
| `edit_file` | FilesystemMiddleware | Sửa file (string replacement) |
| `glob` | FilesystemMiddleware | Tìm file theo pattern |
| `grep` | FilesystemMiddleware | Tìm kiếm nội dung |
| `execute` | FilesystemMiddleware | Chạy shell command |
| `task` | SubAgentMiddleware | Ủy thác tác vụ cho sub-agent |

### 3.3 State Schema: `DeepAgentState`

```python
class DeepAgentState(AgentState):
    messages: Required[Annotated[list[AnyMessage], DeltaChannel(_messages_delta_reducer, snapshot_frequency=50)]]
```

- Sử dụng `DeltaChannel` để tối ưu checkpoint: O(N²) → O(N)
- Snapshot đầy đủ mỗi 50 bước

### 3.4 Middleware Stack (thứ tự)

```
1. TodoListMiddleware
2. SkillsMiddleware               (nếu skills được cung cấp)
3. FilesystemMiddleware           (required scaffolding)
4. SubAgentMiddleware             (required scaffolding)
5. SummarizationMiddleware
6. PatchToolCallsMiddleware
7. AsyncSubAgentMiddleware        (nếu async subagents được cung cấp)
   ├── User middleware             (do người dùng cung cấp)
8. Harness profile extra_middleware
9. _ToolExclusionMiddleware       (nếu profile có excluded_tools)
10. AnthropicPromptCachingMiddleware  (unconditional)
11. MemoryMiddleware              (nếu memory được cung cấp)
12. HumanInTheLoopMiddleware      (nếu interrupt_on được cung cấp)
```

**Required scaffolding (không thể bỏ qua):**
- `FilesystemMiddleware` — File tools + permission enforcement
- `SubAgentMiddleware` — `task` tool handler

### 3.5 System Prompt Assembly

Thứ tự ghép prompt:
```
USER (system_prompt= từ người dùng)
BASE (BASE_AGENT_PROMPT mặc định ~3000 ký tự) hoặc CUSTOM (profile.base_system_prompt)
SUFFIX (profile.system_prompt_suffix, nếu có)
```

`BASE_AGENT_PROMPT` bao gồm:
- Be concise, không preamble thừa
- Professional objectivity
- Task execution: Understand → Act → Verify
- Progress updates cho tác vụ dài

### 3.6 Backends

| Backend | Mô tả |
|---------|-------|
| `StateBackend` | Ephemeral trong LangGraph state (default) |
| `FilesystemBackend` | Đọc/ghi trực tiếp disk |
| `LocalShellBackend` | Shell command local |
| `StoreBackend` | Persistent cross-thread storage |
| `CompositeBackend` | Route theo path prefix |
| `ContextHubBackend` | LangSmith ContextHub |
| `LangSmithSandbox` | LangSmith sandbox execution |

Tất cả implement `BackendProtocol`. Backend có shell implement thêm `SandboxBackendProtocol`.

---

## 4. Profiles System

### 4.1 HarnessProfile

Điều chỉnh hành vi agent SAU KHI model được khởi tạo:

| Field | Mô tả |
|-------|-------|
| `base_system_prompt` | Thay thế BASE_AGENT_PROMPT |
| `system_prompt_suffix` | Text thêm vào cuối system prompt |
| `tool_description_overrides` | Ghi đè mô tả tool |
| `excluded_tools` | Tools bị loại bỏ (additive khi merge) |
| `excluded_middleware` | Middleware bị loại bỏ (union khi merge) |
| `extra_middleware` | Middleware bổ sung (có thể là factory) |
| `general_purpose_subagent` | Cấu hình default subagent |

**Built-in profiles:**
- `anthropic:claude-sonnet-4-6`
- `anthropic:claude-opus-4-7`
- `anthropic:claude-haiku-4-5`
- `openai:codex`

**Merge semantics:**
- Single-value: newest wins
- Tool descriptions: merge dict
- Excluded tools/middleware: union
- Middleware sequences: merge by type
- GP subagent: merge field-wise

### 4.2 ProviderProfile

Điều chỉnh việc KHỞI TẠO model:
- `init_kwargs` — Kwargs cho model initialization
- Pre-init side effects
- Built-in: OpenAI (Responses API), OpenRouter (version check + attribution)

### 4.3 HarnessProfileConfig

Phiên bản khai báo (YAML/JSON) của `HarnessProfile`:
- Không có runtime-only fields (`extra_middleware`)
- `from_dict()` / `to_dict()` cho YAML/JSON

---

## 5. Deep Agents Code (TUI Application)

### 5.1 Cài đặt

```bash
curl -LsSf https://langch.in/dcode | bash
```

### 5.2 Tech Stack

- **UI:** Textual (Python TUI framework)
- **Model Providers:** OpenAI, Anthropic, Google, Ollama, vLLM
- **Sandbox:** OpenAI Codex, LangSmith sandbox
- **MCP:** GitHub, Slack providers

### 5.3 Key Components

| File | Mô tả |
|------|-------|
| `main.py` | CLI entry point |
| `app.py` | Textual app definition |
| `agent.py` | Agent creation & configuration |
| `editor.py` | File editing |
| `file_ops.py` | File operations |
| `tools.py` | Tool definitions |
| `hooks.py` | Shell hooks |
| `_git.py` | Git integration |
| `clipboard.py` | Clipboard support |
| `media_utils.py` | Image/media handling |

---

## 6. CLI (Deployment)

| Lệnh | Mô tả |
|------|-------|
| `deepagents init` | Tạo project scaffold |
| `deepagents dev` | `langgraph dev` local testing |
| `deepagents deploy` | Deploy lên LangGraph Platform |

---

## 7. Agent Context Protocol (ACP)

Cung cấp ACP server wrap quanh Deep Agents:
- `DeepAgentsAcpServer` — ACP server implementation
- Remote clients tạo sessions, send prompts, stream responses
- Content block conversion (text/image/audio/resource)
- Shell command safety analysis (chặn pipe bombs, rm -rf, data exfiltration)

---

## 8. Evaluation Suite

### 8.1 Benchmarks

| Benchmark | Mô tả |
|-----------|-------|
| Tau2 Airline | Vendored từ sierra-research/tau-bench |
| BFCL APIs | Function calling |
| Memory agent | Tau-bench inspired |
| Skills | Skill loading/execution |
| Subagents | Delegation tests |

### 8.2 Infrastructure

- **Wall-time:** `make bench` → pytest-codspeed
- **Memory:** `make bench-memory`
- **Dashboard:** codspeed.io/langchain-ai/deepagents
- **Threshold:** 10% regression
- **Nightly:** Daily cron sweep

---

## 9. Talon Runtime (Experimental)

Long-running agent runtime:
- `TalonHost` — Agent host
- `ChannelAdapter` — Communication abstraction (WhatsApp)
- `PersistentCronScheduler` — Cron jobs
- `VoiceTranscriber` — Voice transcription (Whisper, Parakeet)

---

## 10. Partner Integrations

| Partner | Package | Môi trường |
|---------|---------|------------|
| Daytona | `langchain_daytona` | Cloud sandboxes |
| Modal | `langchain_modal` | Serverless GPU |
| Vercel | `langchain_vercel_sandbox` | Edge sandboxes |
| Runloop | `langchain_runloop` | Sandbox environments |
| QuickJS | `langchain_quickjs` | In-process JS REPL |

QuickJS đặc biệt: CodeInterpreterMiddleware, PTCOption, SwarmSubAgent.

---

## 11. GitHub Action

```yaml
- uses: langchain-ai/deepagents@main
  with:
    prompt: "Fix the bug in src/main.py"
    model: "anthropic:claude-sonnet-4-6"
    memory: true
    timeout: 15
```

---

## 12. Development Guidelines

| Rule | Chi tiết |
|------|----------|
| Package manager | `uv` (không pip/poetry/conda) |
| Linter | `ruff` (ALL rules, line-length 150) |
| Type checker | `ty` |
| Type hints | Bắt buộc trên mọi Python code |
| Docstrings | Google-style |
| Testing | pytest, `asyncio_mode = "auto"` |
| Branch naming | `<user>/<scope>/<description>` |
| Commits | Conventional Commits, scope bắt buộc |
| Public API | Cực kỳ stable, không breaking changes |

---

## 13. So sánh các layer

| Layer | Mức độ | Khi nào dùng |
|-------|--------|-------------|
| LangGraph | Graph runtime | Cần custom orchestration |
| LangChain create_agent | Minimal harness | Chỉ cần agent loop |
| **Deep Agents** | **Full harness** | **Cần filesystem, sub-agents, context management, skills** |

Ba layer hoàn toàn tương thích: có thể pass bất kỳ `CompiledStateGraph` nào vào làm sub-agent.
