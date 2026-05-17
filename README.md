# FaultClaw ⚡
### Adversarial Hardware Verification Agent

> *It doesn't just test your design. It tries to break it.*

## What is FaultClaw?

FaultClaw is an **autonomous multi-agent verification system** that thinks like a verification engineer and attacks like a red team. Feed it a hardware design file. It will find exactly where it breaks — and explain why.

Hardware verification is one of the most critical and most neglected stages of chip design. The industry default is manually written testbenches: slow, incomplete, and only as good as the bugs the engineer already suspects exist. Most student and intermediate hardware projects stop at *"it works for a few inputs."*

**FaultClaw automates the hard part — finding the inputs where it doesn't.**

---

## Demo Results

| Design | Tests | Passed | Failed | Coverage |
|---|---|---|---|---|
| `adder_4bit.v` (correct) | 19 | 19 ✅ | 0 | 100% |
| `adder_4bit_buggy.v` (carry-out bug) | 19 | 13 | 6 ❌ | 68.4% |
| Breakdown Mode | 256 | — | — | Full sweep |

FaultClaw caught all 6 carry-overflow failures in the buggy adder with exact explanations of which input combinations triggered the bug.

---

## The Problem with Manual Verification

| Issue | Impact |
|---|---|
| Slow and labor-intensive | Requires deep domain knowledge just to write useful tests |
| Incomplete by nature | Engineers can only find bugs they already anticipate |
| Happy-path biased | Tests verify expected behavior, not failure conditions |
| Doesn't scale | As designs grow, manual testbench coverage collapses |

---

## How It Works

FaultClaw is a closed-loop pipeline of three coordinated agents powered by NVIDIA Nemotron, running sandboxed inside NemoClaw:

```
┌─────────────────┐     ┌──────────────────────────┐     ┌────────────────────────┐
│  Agent 1        │────▶│  Agent 2                 │────▶│  Agent 3               │
│  Spec Reader    │     │  Adversarial Test Gen    │     │  Verification Judge    │
│                 │     │  (Nemotron core)         │     │                        │
│ • Parse RTL     │     │ • Normal tests           │     │ • Run golden reference │
│ • Extract I/O   │     │ • Edge cases             │     │ • Compare outputs      │
│ • Bit widths    │     │ • Adversarial inputs     │     │ • Log failures + why   │
│ • Topology guard│     │ • Breakdown Mode 🔥      │     │ • Compute coverage %   │
└─────────────────┘     └──────────────────────────┘     └────────┬───────────────┘
                                      ▲                            │
                                      └──── Failure detected ──────┘
                                            (targeted follow-up)
```

### Agent 1 — Spec Reader (`agents/spec_reader.py`)
Ingests an RTL hardware module — Verilog (`.v`/`.sv`), JSON, or YAML — and parses the interface: input names, output names, bit widths, and design intent. Includes a topology guard that rejects invalid designs before they cause crashes downstream. Feeds a validated `DesignSpec` to Agent 2.

### Agent 2 — Adversarial Test Generator (`agents/test_generator.py`)
The core of FaultClaw. NVIDIA Nemotron (`nemotron-3-super-120b-a12b`) reasons about the design and generates three tiers of test cases:

- **Normal** — functional checks across expected input ranges
- **Edge cases** — boundary values, overflow conditions, min/max inputs
- **Adversarial** — inputs specifically crafted to exploit design assumptions

This agent doesn't fill templates. It reasons about *where bugs are most likely to hide.* In Breakdown Mode it sweeps all 256 possible input combinations.

### Agent 3 — Verification Judge (`agents/verification_judge.py`)
Executes every test against a Python golden reference model, compares actual vs. expected outputs, and logs failures with precise explanations — including which exact bit and overflow condition triggered each failure. Computes coverage metrics and on failure detection triggers Agent 2 to generate a targeted follow-up suite, **creating a feedback loop that gets smarter with every iteration.**

---

## 🔥 Breakdown Mode

When enabled, Agent 2 stops generating representative tests and **systematically dismantles the design's assumptions**:

- Sweeps all 256 input combinations (full 16×16 space for a 4-bit adder)
- Maximizes overflow conditions at every boundary
- Chains input sequences engineered to expose hidden failure states
- Nemotron identifies highest-risk inputs based on design structure

```bash
python3 main.py --design-spec samples/adder_4bit.v --breakdown
```

> Breakdown Mode turns FaultClaw from a verification tool into an adversarial red team — the kind of thinking that catches bugs before silicon is taped out.

---

## NemoClaw Sandbox

The entire FaultClaw pipeline runs sandboxed inside **NVIDIA NemoClaw** with Landlock + seccomp + network namespace isolation:

```
Sandbox:  faultclaw (Landlock + seccomp + netns)
Model:    nvidia/nemotron-3-super-120b-a12b
Policy:   Balanced — NVIDIA API + pypi + telegram allowed, everything else blocked
```

This isn't just a security checkbox — it's architecturally correct for hardware verification:

- Proprietary circuit designs are **sensitive IP that should never leave the device**
- NemoClaw's policy engine enforces exactly which network endpoints the agent can reach
- Full audit trail of every file access and network call the agent makes
- Positions FaultClaw for real enterprise DV workflows where data security is non-negotiable

```bash
# Start the sandboxed agent
nemoclaw faultclaw connect
openclaw tui
```

---

## Persistent Memory

FaultClaw accumulates knowledge across runs in `memory/history.json`:

```json
{
  "timestamp": "2026-05-16T...",
  "design_name": "adder_4bit",
  "mode": "normal",
  "total_tests": 19,
  "tests_passed": 19,
  "tests_failed": 0,
  "failed_tests": []
}
```

Every run appends a new record. The `failure_patterns()` function surfaces deduplicated failure inputs across all history — ready to seed future Agent 2 runs. **The more FaultClaw runs, the better it gets at targeting bugs.**

---

## Telegram Interface

FaultClaw delivers results in real time via Telegram bot:

| Command | Action |
|---|---|
| `/verify` | Run normal verification on the correct 4-bit adder |
| `/breakdown` | Run full 256-test adversarial sweep |
| `/buggy` | Run against the buggy adder — catches all 6 carry failures |

---

## Project Structure

```
faultclaw/
├── agents/
│   ├── __init__.py
│   ├── spec_reader.py          # Agent 1 — RTL/JSON/YAML parsing, topology guard
│   ├── test_generator.py       # Agent 2 — Nemotron adversarial test generation
│   └── verification_judge.py  # Agent 3 — golden reference model, coverage metrics
├── memory/
│   ├── __init__.py
│   └── store.py                # JSON persistence — run history, failure patterns
├── bot/
│   └── telegram_bot.py         # Telegram bot — /verify /breakdown /buggy
├── samples/
│   ├── adder_4bit.v            # Correct 4-bit adder — all tests pass
│   ├── adder_4bit_buggy.v      # Buggy adder — carry-out hardwired to 0
│   ├── agent1_adder_spec.json  # JSON spec format reference
│   └── failure_feedback.json  # Agent 3 feedback format reference
├── tests/
│   └── test_generator_test.py
├── .env.example
├── main.py                     # Pipeline orchestrator
└── requirements.txt
```

---

## Technology Stack

| Component | Technology |
|---|---|
| AI Model | NVIDIA Nemotron 3 Super 120B (`nemotron-3-super-120b-a12b`) |
| Inference API | NVIDIA NIM — `integrate.api.nvidia.com/v1` |
| Sandbox | NVIDIA NemoClaw — Landlock + seccomp + netns isolation |
| Agent Runtime | OpenClaw inside NemoClaw sandbox |
| Interface | Telegram bot via `python-telegram-bot` |
| Verification Engine | Python golden reference model + output comparator |
| Memory Layer | JSON persistence — run history, failure patterns |
| Target Design | 4-bit adder RTL — scalable to ALUs, FSMs, pipelined processors |

---

## Getting Started

### Prerequisites

```
Python 3.10+
NVIDIA API key  →  build.nvidia.com/models?q=nemotron
Telegram token  →  @BotFather on Telegram
NemoClaw        →  curl -fsSL https://nvidia.com/nemoclaw.sh | bash
Docker          →  required for NemoClaw sandbox
```

### Installation

```bash
git clone https://github.com/re1tub/FaultClaw.git
cd FaultClaw
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env:
# NVIDIA_API_KEY=nvapi-...
# TELEGRAM_BOT_TOKEN=...
```

### Run the pipeline

```bash
# Normal verification — 19 tests, 100% coverage on correct adder
python3 main.py --design-spec samples/adder_4bit.v

# Breakdown Mode — full 256-test adversarial sweep
python3 main.py --design-spec samples/adder_4bit.v --breakdown

# Buggy adder — FaultClaw catches 6 carry-overflow failures
python3 main.py --design-spec samples/adder_4bit_buggy.v --buggy
```

### Run the Telegram bot

```bash
python3 bot/telegram_bot.py
```

### Start the NemoClaw sandbox

```bash
NEMOCLAW_SANDBOX_GPU=0 nemoclaw onboard --no-gpu
nemoclaw faultclaw connect
openclaw tui
```

---

## Team

| Person | Role |
|---|---|
| P1 | Agent 2 — Nemotron prompting, adversarial test generation, Breakdown Mode |
| P2 | Agent 3 — golden reference model, verification engine, coverage metrics, feedback loop |
| P3 | Agent 1 + pipeline orchestration + NemoClaw sandbox + Telegram bot + memory layer |

---

## Future Scope

FaultClaw is scoped to a 4-bit adder for the hackathon. The architecture scales directly to:

- Complex RTL — ALUs, finite state machines, pipelined processors
- Automated SystemVerilog and UVM testbench generation
- Integration with real industry DV flows and EDA toolchains
- Multi-design regression testing across an entire IP library
- Formal verification hints from Nemotron to guide downstream tools

---

## What FaultClaw Is Not

FaultClaw is **not a chatbot.**

It is a working autonomous verification pipeline that produces real engineering artifacts — test suites, coverage reports, and failure diagnoses — on real hardware designs, inside a secure NemoClaw sandbox.

---

