# FaultClaw: Project Design Document
### Dontae Butler
Computer Engineering BS, University Of California - Santa Cruz
### Isaac Hashimi
Electrical Engineering BS, University Of California - Santa Cruz
### Ibrahim Jarada
Electrical Engineering BS, University Of California - Santa Cruz

## Abstract

This design document extends the FaultClaw final project report by presenting the motivation, architecture, and implementation of an AI-assisted register-transfer level (RTL) verification framework. Functional verification is essential for ensuring that digital hardware designs behave according to their intended specifications before physical implementation. However, traditional verification workflows require substantial engineering effort to develop testbenches, identify corner cases, execute simulations, and diagnose functional errors. Recent advancements in large language models (LLMs) have introduced opportunities to automate selected aspects of these workflows.

Developed as part of an NVIDIA hackathon, FaultClaw is an AI-assisted RTL verification framework that incorporates NemoClaw, an AI agent provided by NVIDIA for the event. The project explores the use of NemoClaw to support automated test generation, verification execution, and functional error detection. By integrating AI-assisted automation into the verification workflow, FaultClaw aims to reduce manual engineering effort while maintaining a systematic approach to evaluating RTL correctness.

## 1. Introduction

Functional verification is a critical stage in the digital hardware design process, ensuring that register-transfer level (RTL) implementations behave according to their intended specifications before physical implementation. As hardware designs increase in complexity, developing comprehensive testbenches, identifying corner cases, and diagnosing functional errors require substantial engineering effort [1]. Traditional verification methodologies employ directed testing, constrained-random stimulus generation, and simulation-based analysis to evaluate design correctness [2]. Although these techniques are widely adopted and effective, constructing and maintaining comprehensive verification environments remains a significant engineering challenge.

Recent advancements in large language models (LLMs) have introduced opportunities to automate aspects of hardware verification, particularly testbench generation and evaluation [3]. Motivated by these developments, this project introduces FaultClaw, an AI-assisted RTL verification framework designed to automate test generation, execute verification workflows, and identify potential functional discrepancies in hardware designs.

### 1.1 Problem Statement

Functional verification presents a significant challenge in digital hardware development due to the complexity of identifying errors within register-transfer level (RTL) designs. Although simulation-based verification allows engineers to evaluate hardware behavior before physical implementation, its effectiveness depends heavily on the quality and completeness of the applied test cases. An RTL implementation may exhibit correct behavior under typical operating conditions while containing functional errors that become apparent only under specific input combinations or corner cases. Consequently, developing comprehensive verification environments requires engineers to construct meaningful test scenarios, establish expected outputs, and analyze simulation results.

Traditional verification workflows often involve substantial manual effort in test development, simulation execution, and failure analysis. Although existing verification methodologies provide effective approaches for evaluating RTL correctness, constructing and maintaining these environments can become increasingly demanding as design complexity grows. These challenges motivate the exploration of automated techniques capable of assisting engineers with selected verification tasks.

FaultClaw addresses this problem by investigating an AI-assisted RTL verification workflow that integrates automated test generation, simulation execution, and evaluation of observed hardware behavior. The primary objective is to reduce the manual effort associated with these tasks while maintaining a structured process for identifying potential functional discrepancies. Rather than replacing established verification methodologies, FaultClaw explores how AI-assisted automation can complement existing approaches to hardware functional verification.

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
