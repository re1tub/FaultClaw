# FaultClaw: Project Design Document
### Dontae Butler
Computer Engineering BS, University Of California - Santa Cruz
### Isaac Hashimi
Electrical Engineering BS, University Of California - Santa Cruz
### Ibrahim Jarada
Electrical Engineering BS, University Of California - Santa Cruz

## Abstract

This Design Document is an extension of the FaultClaw final project report. This paper briefly introduces how functional verification is essential to ensuring RTL design correctness. We examine how traditional verification methods require significant engineering effort to develop testbenches, identify edge cases, and diagnose bugs. Recent advances in Large Language Models (LLMs) offer opportunities to automate this process. FaultClaw addresses these challenges by introducing NemoClaw, an autonomous, high-reasoning assistant that automates test generation, simulation workflows, and functional error detection to improve verification efficiency and reduce workload.

## 1. Introduction

Functional verification is a critical stage in the digital hardware design process, ensuring that register-transfer level (RTL) implementations behave as intended before physical implementation. As hardware designs increase in complexity, developing testbenches, identifying corner cases, and diagnosing functional errors demand substantial effort [1]. Traditional verification methodologies rely on directed testing, constrained-random stimulus generation, and simulation-based analysis to determine the correctness of a design[2]. However, these techniques are widely adopted; constructing and maintaining effective verification environments remains a significant hurdle. Recent advancements in LLMs have introduced opportunities to automate aspects of hardware verification, particularly testbench generation and evaluation [3]. Motivated by these develops, this project introduces **FaultClaw**, an AI-assisted RLT verification framework designed to automate test generation, execute verification workflows, and identify potential functional discrepancies in hardware designs.

### 1.1 Problem Statement

Functional verification presents a significant challenge in digital hardware devlopment due to the complexity of idenitifying errors within register-transfer level(RTL) designs. Althought simulation-basedverification allows engineers to evaluate hardware behavior before physical implementation, its effectiveness depends heavily on the entireness of the test cases being applied. RTL implementation may exhibit correct behavior under typical operating conditions while containing functional errors that become apparent only under specific inputs or corner cases. Consequently, developing comprehessive verification enviroments requires engineers to construct meaningful test scenarios, establish expected outpus, and analyze simulation results.

FaultClaw attempts to address the issues that come with traditional verification workflows, typically involving substantial efforts, excutiable test, and acknowlaging failures. Although current methodologies and workflow are effective, they are often very demanding and grow increasingly harder as design complexity grows. These challenges motivate FaultClaw to explore an AI-Assisted RTL verification workflow. Through implementiaon of automated test geneation, sumulation and evaluation hardware. The objective is to reduce the manual efforts and demand associated with selected verification task while mainting effectiveness.

### 1.2 Project Objectives



### 1.3 Scope and Limitations

## 2. System Architecture
### 2.1 High-Level Overview
### 2.2 Agent Architecture
### 2.3 Data Flow

## 3. Design and Implementation

## 4. Verification Methodology

## 5. Experimental Results

## 6. Design Tradeoffs and Limitations

## 7. Future Work

## 8. References

## 9. Conclusion

## 10. Work Contribution
