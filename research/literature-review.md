# Literature Review: LLM for Network Configuration & Troubleshooting

> Generated via deep research (June 2026). 19 confirmed claims from 24 sources, adversarially verified.

---

## Key Finding: LLMs Are Promising but Fundamentally Unreliable Without Augmentation

On low-level device configuration (OSPF, BGP, RIP), GPT-4 produces error-free output in only **1 of 3 runs** without RAG. With RAG, accuracy approaches 100% except for OSPF. On realistic large-scale queries, AI agents achieve only **13–38%** average performance, with worst-case as low as 3%.

## 1. Reliability Problems

| Issue | Detail |
|---|---|
| **Low-level config errors** | GPT-4 error-free in 1/3 runs on OSPF/RIP/BGP/RIFT |
| **Basic mistakes** | IP addressing, subnet mask conversion, numeric notation — fluent but wrong |
| **Transitive conflicts** | Cannot detect indirect contradictions (e.g., "s1→h2 via s2" + "s2 cannot reach h2") |
| **Regression on repair** | LLMs introduce new errors when fixing misconfigurations |
| **Scale degradation** | Performance drops sharply as topology grows (20→754 nodes) |

### Sources
- [NetConfEval](https://dl.acm.org/doi/10.1145/3656296) — Wang et al., CoNEXT 2024 (won 2025 IRTF Applied Networking Research Prize)
- [NetArena](https://arxiv.org/abs/2506.03231) — Zhou et al., ICLR 2026
- [Anwar & Caesar](https://dl.acm.org/doi/10.1145/3717512.3717515) — SIGCOMM CCR 2025, Best of CCR
- [Lost in Transmission](https://arxiv.org/abs/2505.08140) — 2025

## 2. Existing Evaluation Frameworks

### NetConfEval (CoNEXT 2024, Red Hat/KTH)

Four-stage pipeline:
1. Requirement formalization (NL → formal specs)
2. API translation (formal specs → API calls)
3. Routing algorithm generation (as code)
4. Low-level device configuration (with RAG support)

- Uses FRRouting (vtysh) and Kathara emulator
- [Open-source code](https://github.com/RedHatResearch/conext24-NetConfEval)
- Dataset on HuggingFace

### NetConfBench (IETF NMRG Draft, Dec 2025)

- **40 JSON-defined tasks** spanning routing, QoS, and security
- **Three evaluation metrics**:
  - **Reasoning score**: embedding cosine similarity with reference answer
  - **Command score**: hierarchical `ciscoconfparse` diff with F1
  - **Testcase score**: proportion of passed verification checks
- Runs on **GNS3** with official vendor images
- Agent-Network Interface: `get-topology`, `get-running-cfg`, `update-cfg`, `execute-cmd`
- [IETF Draft v01](https://datatracker.ietf.org/doc/draft-cui-nmrg-llm-benchmark/01/)

## 3. Troubleshooting

### Cornetto Benchmark (ETH Zurich, Apr 2026)

- 9 SOTA LLMs tested on 231 synthesized misconfiguration problems
- Topologies from 20–754 nodes
- Formal verification used as ground truth
- **LLMs frequently introduce regressions**; iterative feedback helps only slightly
- [arXiv:2604.22513](https://browse-export.arxiv.org/abs/2604.22513)

### Key Insight

Reliable LLM-powered network automation requires integrating LLMs into **iterative, closed-loop workflows guided by formal verification** — not one-shot autonomous fixes.

## 4. Real-World Complexity

- **37.7%** of 11,088 ACLs in a university campus network contain conflicting rule overlaps
- **27%** of conflicted ACLs have >20 conflicts
- ~29% of cloud ACLs show overlaps

Source: Mondal et al., HotNets 2025 (UCLA + Microsoft Research)

## 5. Promising Direction: Multi-Agent Architectures

Multi-agent LLM architectures that decompose natural-language network configuration tasks into subtasks via specialized agents represent a promising approach:
- ConfAgent (IWQoS 2025): dedicated Conflict Detector + Formal Synthesizer agents
- CoTNet (2025): template generation → parameter assignment
- Rozsival et al. (IEEE NCA 2025): explicit multi-agent decomposition

## 6. The Gap: MCP Integration

**No existing benchmark or framework integrates the MCP (Model Context Protocol) standard** for LLM-to-network-device communication. NetConfEval, NetConfBench, Cornetto, and NetArena all use custom Agent-Network Interfaces or direct API calls.

Our FYP's use of [Cisco CML's MCP server](https://github.com/xorrkaz/cml-mcp) to bridge LLMs with network devices fills a **genuine gap** in the research landscape.

## 7. MCP-Related IETF Drafts

- [MCP for Network Troubleshooting](https://www.ietf.org/archive/id/draft-zm-rtgwg-mcp-troubleshooting-00.xml)
- [MCP for Network Management](https://datatracker.ietf.org/doc/html/draft-zw-opsawg-mcp-network-mgmt-00)

## 8. Cisco Resources

- [CML MCP Server (GitHub)](https://github.com/xorrkaz/cml-mcp)
- [Cisco Blog: AI-Driven CML with MCP](https://blogs.cisco.com/learning/speak-your-lab-into-existence-with-ai-driven-cisco-modeling-labs-and-mcp)
- [CML User Guide](https://developer.cisco.com/docs/modeling-labs/#!cml-users-guide)

---

## Open Questions for Our FYP

1. How does Cisco CML's MCP server compare to NetConfBench's custom Agent-Network Interface in terms of latency, reliability, and LLM usability?
2. Can iterative formal-verification-guided workflows from Cornetto be integrated with the MCP-based CML interface?
3. Do NetConfEval/NetConfBench findings generalize from GNS3/Kathara to physical Cisco hardware via CML?
4. What is the minimum viable prompting/RAG strategy for reliable L2/L3 configurations on 10–50 node CML topologies?
