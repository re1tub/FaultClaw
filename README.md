# FaultClaw ⚡
### Adversarial Hardware Verification Agent

> *It doesn't just test your design. It tries to break it.*
---

## What is FaultClaw?

FaultClaw is an **autonomous multi-agent verification system** that thinks like a verification engineer and attacks like a red team. Feed it a hardware design. It will find where it breaks.

Hardware verification is one of the most critical — and most neglected — stages of chip design. The industry default is manually written testbenches: slow, incomplete, and only as good as the bugs the engineer already suspects exist. Most student and intermediate hardware projects stop at *"it works for a few inputs."*

**FaultClaw automates the hard part — finding the inputs where it doesn't.**

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

FaultClaw is a closed-loop pipeline of three coordinated OpenClaw agents, each powered by NVIDIA Nemotron:

```
┌─────────────────┐     ┌──────────────────────────┐     ┌────────────────────────┐
│  Agent 1        │────▶│  Agent 2                 │────▶│  Agent 3               │
│  Spec Reader    │     │  Adversarial Test Gen    │     │  Verification Judge    │
│                 │     │  (Nemotron core)         │     │                        │
│ • Parse RTL     │     │ • Normal tests           │     │ • Run golden reference │
│ • Extract I/O   │     │ • Edge cases             │     │ • Compare outputs      │
│ • Map behavior  │     │ • Adversarial inputs     │     │ • Log failures         │
│ • Build spec    │     │ • Breakdown Mode 🔥      │     │ • Compute coverage     │
└─────────────────┘     └──────────────────────────┘     └────────┬───────────────┘
                                      ▲                            │
                                      └──── Failure detected ──────┘
                                            (feedback loop)
```

### Agent 1 — Spec Reader
Ingests an RTL hardware module, parses the interface (inputs, outputs, bit widths), and builds a structured internal representation of the design's intended behavior. This context feeds everything downstream.

### Agent 2 — Adversarial Test Generator
The core of FaultClaw. Nemotron reasons about the design and generates three tiers of test cases:

- **Normal** — functional checks across expected input ranges
- **Edge cases** — boundary values, overflow conditions, min/max inputs
- **Adversarial** — inputs specifically crafted to exploit design assumptions

This agent doesn't fill templates. It reasons about *where bugs are most likely to hide.*

### Agent 3 — Verification Judge
Executes every test against a golden reference model, compares actual vs. expected outputs, logs failures with precise explanations, and computes coverage metrics. On failure detection, it triggers Agent 2 to generate a follow-up suite targeting the failure zone — **creating a feedback loop that gets smarter with every iteration.**

---

## 🔥 Breakdown Mode

The standout feature. When enabled, the gloves come off.

Agent 2 stops generating polite tests and **systematically dismantles the design's assumptions**:

- Maximizes overflow conditions across all input combinations
- Stresses boundary values at every bit-width limit
- Chains input sequences specifically engineered to expose hidden failure states
- Prioritizes inputs Nemotron identifies as highest-risk based on the design structure

> Breakdown Mode turns FaultClaw from a verification tool into an adversarial red team — the kind of thinking that catches bugs before silicon is taped out.

---

## Architecture

```
faultclaw/
├── agents/
│   ├── spec_reader.py          # Agent 1 — RTL parsing, interface extraction
│   ├── test_generator.py       # Agent 2 — Nemotron-powered test generation
│   └── verification_judge.py  # Agent 3 — golden model execution, coverage
├── reference_models/
│   └── adder_golden.py         # Software reference implementation
├── memory/
│   └── store.py                # OpenClaw persistent memory layer
├── bot/
│   └── telegram_bot.py         # Real-time interface
├── sandbox/
│   └── nemoclaw_config.py      # NemoClaw policy configuration
└── main.py                     # Pipeline orchestration
```

---

## Technology Stack

| Component | Technology |
|---|---|
| Agent Framework | OpenClaw — persistent, multi-agent, always-on orchestration |
| AI Model | NVIDIA Nemotron — adversarial reasoning and test generation |
| Sandbox | NVIDIA NemoClaw — on-device execution, policy-based security |
| Compute | NVIDIA Brev — cloud GPU instances |
| Interface | Telegram bot — real-time interaction and result delivery |
| Verification Engine | Python golden reference model + output comparator |
| Target Design | 4-bit adder RTL (scalable to ALUs, FSMs, pipelined processors) |
| Memory Layer | OpenClaw persistent store — design history, failure patterns |

---

## Why NemoClaw Sandboxing?

Running inside NemoClaw isn't just a security checkbox — it's architecturally correct:

- Proprietary circuit designs are **sensitive IP that should never leave the device**
- Nemotron inference runs fully local — zero design data transmitted externally
- NemoClaw's policy engine controls filesystem and network access during every run
- Positions FaultClaw for real enterprise design verification workflows

---

## Persistent Memory

OpenClaw's always-on memory layer means FaultClaw is not a one-off script. Between runs it accumulates:

- Full test history and failure logs per design
- Which test patterns were most effective at finding bugs
- Coverage gaps that remain unaddressed
- Design iteration history for automatic regression verification

**The more FaultClaw runs, the better it gets at finding bugs.**

---

## Live Demo

| Step | What Happens |
|---|---|
| 1 | Submit a correct 4-bit adder → all tests pass cleanly |
| 2 | Enable Breakdown Mode → watch adversarial inputs generated live by Nemotron |
| 3 | Swap in a deliberately buggy adder → FaultClaw catches the failure automatically |
| 4 | Observe the feedback loop — Agent 3 flags failure, Agent 2 doubles down on that region |
| 5 | View the structured failure report with coverage metrics and exact failure explanations |

---

## Getting Started

### Prerequisites

```bash
python >= 3.10
nvidia-brev          # Brev CLI for GPU instance provisioning
python-telegram-bot  # Telegram interface
```

### Installation

```bash
git clone https://github.com/your-org/faultclaw.git
cd faultclaw
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Add your Telegram bot token, Brev API key, and NemoClaw config
```

### Run

```bash
python main.py --design designs/adder_4bit.v
python main.py --design designs/adder_4bit.v --breakdown  # Enable Breakdown Mode
```

---

## Future Scope

FaultClaw is scoped to a 4-bit adder for the hackathon. The architecture is designed to scale:

- Complex RTL — ALUs, finite state machines, pipelined processors
- Automated SystemVerilog and UVM testbench generation
- Integration with real industry DV flows and EDA toolchains
- Multi-design regression testing across an entire IP library
- Formal verification hints from Nemotron to guide downstream tools

---

## What FaultClaw Is Not

FaultClaw is **not a chatbot.**

It is a working autonomous verification pipeline that produces real engineering artifacts — test suites, coverage reports, and failure diagnoses — on real hardware designs.

---

*Built at UCSC Baskin School of Engineering for the NVIDIA × OpenClaw Hackathon.*