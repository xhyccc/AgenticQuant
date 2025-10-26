# **Architecting an Autonomous Quantitative Finance Multi-Agent System: A Technical Deep Dive**

## **Introduction and Foundational Paradigms**

This report provides a comprehensive architectural blueprint for a sophisticated multi-agent system designed to automate the discovery, development, and refinement of quantitative trading strategies. Leveraging HTTP-based Large Language Model (LLM) APIs, this system is engineered to operate with a high degree of autonomy, adaptability, and analytical rigor. The architecture is founded upon two core paradigms: the ReAct (Reasoning and Acting) framework for agent cognition and a Multi-Agent System (MAS) structure for organizational scalability and specialization. This combination is not an arbitrary choice but a deliberate design decision to create a digital analogue of a high-performing human quantitative research team, addressing the unique challenges of the financial domain.

### **The Mandate: Automating Quantitative Strategy Discovery**

The primary objective of this system is to autonomously ideate, develop, backtest, and iteratively refine quantitative trading strategies in response to high-level user directives. The domain of quantitative finance presents a formidable challenge for automation. Financial markets are complex, non-stationary systems characterized by high signal-to-noise ratios and rapidly changing dynamics. Traditional machine learning and deep learning models, while powerful, often exhibit brittleness in this context; they can overfit to historical data and fail to adapt to new market regimes.¹ This necessitates a system that can not only perform complex calculations but also reason about its actions, adapt its strategy based on new evidence, and explain its decision-making process.

The proposed system is designed to tackle this complexity by moving beyond static model execution. It aims to replicate the end-to-end workflow of a quantitative researcher: forming a hypothesis, gathering and processing data, building and testing a model, critically evaluating the results, and refining the approach based on those results. By automating this iterative cycle, the system can explore the vast search space of potential trading strategies more efficiently and systematically than manual human efforts alone.

### **The Cognitive Core: ReAct (Reasoning and Acting)**

The fundamental cognitive architecture for every agent within this system is the ReAct framework.² ReAct synergizes the reasoning capabilities of LLMs, often exemplified by Chain-of-Thought (CoT) prompting, with the ability to take concrete actions by interacting with external tools.² This paradigm is structured around an iterative loop of **Thought \-\> Action \-\> Observation**.⁴

1. **Thought**: The agent generates a verbalized reasoning trace, breaking down a complex problem into a manageable next step and forming a plan to execute it.²  
2. **Action**: Based on its thought process, the agent formulates a specific action, typically a call to an external tool or API.⁴  
3. **Observation**: The agent executes the action and receives an observation from the environment—the result of the tool call. This new information is then fed back into the agent's context for the next thought step, creating a powerful feedback loop.⁵

This structure provides several critical advantages over simpler prompting techniques. A significant limitation of CoT reasoning alone is its susceptibility to "fact hallucination," where the model confidently generates plausible but incorrect information due to its lack of access to the external world.⁴ ReAct directly mitigates this risk by grounding the agent's reasoning process in real-time, factual information retrieved from external tools, such as financial data APIs or web search results.² This grounding dramatically improves the accuracy and trustworthiness of the agent's outputs, a non-negotiable requirement in the precise world of quantitative finance.

Furthermore, the explicit reasoning traces generated in the "Thought" step provide a high degree of explainability and interpretability.² For a complex system developing financial strategies, the ability to audit the agent's step-by-step logic is paramount for debugging, validation, and building trust with human stakeholders. If a strategy fails, analysts can inspect the agent's thought process to understand precisely where its reasoning went astray.

The implementation of ReAct has evolved significantly since its inception. The original framework relied on prompting the LLM to generate a specific text format that was then parsed to extract the tool call.⁴ Modern LLMs now support native "function calling" or "tool calling," allowing them to generate structured JSON outputs that directly correspond to a tool's API signature.³ This modern approach is far more robust and reliable, eliminating the brittleness of text parsing and ensuring that actions are executed with precision.⁶ This system will leverage this modern, tool-calling implementation of the ReAct paradigm.

### **The Organizational Structure: Multi-Agent Systems (MAS)**

While a single, powerful ReAct agent can accomplish complex tasks, a monolithic approach often encounters limitations related to context window size, cognitive overload, and the need for diverse, specialized skills.⁸ To overcome these challenges, this system is designed as a Multi-Agent System (MAS), a collaborative network of specialized agents working in concert to achieve a common goal.¹¹

The rationale for adopting a MAS architecture is rooted in the principle of task decomposition and specialization.¹³ A complex quantitative finance workflow can be broken down into distinct sub-tasks, each requiring a different expertise: high-level planning, data retrieval, code execution for analysis, critical evaluation, and final report generation. Assigning these tasks to specialized agents offers numerous benefits:

* **Modularity and Scalability**: Each agent is a self-contained component with a clearly defined role. This makes the system easier to develop, test, and maintain. New capabilities can be added by introducing new agents or tools without re-architecting the entire system.¹⁴  
* **Domain Specialization**: Agents can be fine-tuned or prompted with highly specific instructions and personas, making them experts in their narrow domain. A Planner agent can be optimized for logical decomposition, while a Writer agent can be optimized for narrative synthesis.¹³ This leads to higher-quality outputs at each stage of the workflow.  
* **Robustness and Reliability**: By distributing tasks, the system avoids a single point of failure. If one agent encounters an error, its impact can be contained, and the orchestrating agent can potentially re-route the task or attempt a recovery strategy.¹⁵  
* **Efficiency**: Specialized agents can operate in parallel where the workflow allows, reducing the overall time to completion. The context window for each agent is also more focused, containing only the information relevant to its immediate task, which can improve performance and reduce costs.⁸

The design of this multi-agent system is a direct digital analogue of a successful human workflow. A human quantitative research team is not a collection of generalists; it is a structured team of specialists. There is typically a lead researcher or portfolio manager who defines the overall direction (the **Orchestrator**), senior quants who devise research plans (the **Planner**), junior analysts or data scientists who execute the analyses and run backtests (the **Executor**), and a risk committee or peer review group that critiques the final strategy (the **Judger**). By mirroring this proven collaborative structure, the MAS architecture leverages the principles of division of labor and specialized expertise that are fundamental to solving complex, open-ended problems in domains like quantitative finance.

## **System Architecture: A Supervisor-Driven Blueprint**

The high-level architecture of the system is designed for clarity, control, and auditability. It employs a centralized orchestration pattern, a standardized communication protocol for tool interaction, and a novel file-based approach to context and state management. This combination ensures that the complex, multi-step process of quantitative strategy generation is executed in a structured, traceable, and resilient manner.

### **The Orchestration Pattern: Supervisor-Worker Model**

The system's organizational structure is formally defined as a **Supervisor-Worker** model, also referred to as an Orchestrator-Worker or Hierarchical architecture.⁸ In this pattern, a single, central agent—the **Master/Orchestrator**—acts as the supervisor, while all other agents (Planner, Executor, Writer, etc.) function as specialized workers.

This choice of a centralized control flow is deliberate. The Orchestrator receives the initial user request and is solely responsible for managing the entire workflow. It delegates specific subtasks to the appropriate worker agents, awaits their completion, integrates their outputs into the shared context, and determines the next step based on a predefined plan or dynamic conditions.¹¹ This contrasts with decentralized or network-based architectures where any agent can communicate with any other agent.⁸ For a goal-oriented and high-stakes task like financial analysis, a clear, hierarchical chain of command provides superior reliability, predictability, and auditability.⁹ Modern agentic frameworks like LangGraph are explicitly designed to facilitate the construction of such supervised, graph-based workflows, where agents are nodes and the supervisor directs the flow of execution along the graph's edges.⁸

The following diagram illustrates the high-level control and data flow within the system. The Master/Orchestrator serves as the central hub, directing the sequential execution of tasks and managing the iterative strategy refinement sub-loop.

### **The Communication Backbone: Model Context Protocol (MCP)**

To ensure robust and standardized interaction between the agents and their diverse toolset, the system will implement the **Model Context Protocol (MCP)** as its communication backbone.¹⁹ MCP is an open specification designed to standardize how context is passed between LLMs and external applications, services, and tools.¹⁹ It provides a structured message format that clearly delineates different types of information, such as system instructions, user messages, assistant responses, tool calls, and tool outputs.¹⁹

The adoption of MCP is a critical design choice that moves beyond ad-hoc JSON or simple text-based communication. The benefits are manifold:

* **Reduced Ambiguity**: The structured format ensures that both the agent and the tool have an unambiguous understanding of the request and response, minimizing parsing errors that could have significant financial consequences.  
* **Enhanced Security**: MCP's explicit structure for authentication and metadata allows for more secure and controlled interactions with tools.¹⁹  
* **Interoperability and Extensibility**: By adhering to an open standard, the system becomes platform-agnostic. New tools, whether developed in-house or provided by third parties, can be integrated seamlessly as long as they expose an MCP-compliant endpoint. This "plug-and-play" characteristic is vital for a system that must evolve with the availability of new financial data sources and analytical techniques.¹⁹

It is important to distinguish MCP from Agent-to-Agent (A2A) protocols. While A2A protocols are designed to govern direct communication and collaboration *between* autonomous agents from different providers, MCP is focused on the interface *between an agent and its tools*.²⁰ In this architecture, inter-agent communication is implicitly handled by the Orchestrator, which acts as the central message broker. The explicit communication protocol, MCP, is used at the agent-tool boundary, ensuring that every action taken by the system is a well-defined, structured, and secure event.

### **The System's Memory: File-Based Context Management**

One of the most significant challenges in multi-agent systems is maintaining a coherent, shared context across multiple steps and interactions, a problem often termed the "disconnected models problem".²⁴ LLMs are inherently stateless, and their context windows are finite. To overcome this, the system employs a robust external memory strategy centered on the local file system.

The mechanism is as follows:

1. **Session Initialization**: Upon receiving a new user request, the system immediately creates a unique, timestamped subfolder within a main project directory (e.g., /requests/2025-10-20\_12-28-05\_AAPL\_momentum\_strategy/). This folder becomes the dedicated, persistent workspace for the entire lifecycle of that request.  
2. **Artifact Persistence**: Every artifact generated by any agent or tool during the workflow is saved as a file in this dedicated subfolder. This includes the initial plan (plan.json), web search results (search\_results.txt), downloaded financial data (AAPL\_daily.csv), generated Python code for strategies (strategy\_v1.py), backtest results (results\_v1.json), analytical charts (sharpe\_over\_time.png), and the final report (final\_report.md).  
3. **Contextual State Awareness**: The Master/Orchestrator agent's primary state-management function is to periodically execute a scan\_directory tool. The output of this tool—a list of filenames, their creation timestamps, and sizes—serves as a compact summary of the current state of the project. This summary is injected into the Orchestrator's context window. This "just-in-time" approach to context loading is highly efficient; instead of flooding the LLM's context with the raw content of large data files, it provides lightweight identifiers (filenames) that the agent can reason about and decide to load on demand using other tools.²⁵

This file-based approach to context management offers profound advantages. First, it provides a complete, human-readable audit trail of the entire process. Every piece of data used, every line of code executed, and every result generated is preserved and traceable. Second, it makes the system inherently stateless and resilient. The state is not held in memory but on disk. If any part of the system crashes, the workflow can be resumed by simply re-initializing the Orchestrator and having it scan the directory to reconstruct the current state.

The combination of the Supervisor architecture for centralized control, MCP for structured tool interactions, and a file-based system for external memory creates an architecture that is not merely functional but also inherently auditable, transparent, and resilient. The centralized control flow ensures that every major decision is logged and traceable back to the Orchestrator. The externalized file system provides a complete, persistent record of the workflow's history that can be inspected by a human auditor or regulator at any time. This design directly addresses the non-functional requirements of transparency and traceability that are paramount for deploying advanced AI systems within highly regulated industries like finance.

## **The Agent Roster: Specialized Roles and Prompt Engineering**

The efficacy of the multi-agent system hinges on the precise definition and implementation of each specialized agent. An agent's behavior is primarily governed by its prompt, which establishes its persona, delineates its responsibilities, lists its available tools, and constrains its output format. This section provides a granular breakdown of each agent's design and the prompt engineering strategies required to guide its behavior.

### **Master/Orchestrator Agent**

* **Role**: The Master/Orchestrator is the central nervous system and project manager of the entire operation.¹¹ It does not perform domain-specific tasks itself but instead manages the state and flow of the entire workflow. Its core responsibilities include: receiving the initial user query, delegating the planning task to the Planner, interpreting the generated plan, dispatching discrete tasks from the plan to the Executor in sequence, managing the iterative refinement loop, and finally, commissioning the report from the Writer. It is the sole agent responsible for routing control between other agents, acting as the central hub in the supervisor-worker model.⁸  
* **Prompting**: The Orchestrator's prompt is meta-level, focusing on workflow management and decision-making rather than content generation. The key components of its prompt are the overall goal, the current plan, and a summary of the working directory's contents, which represents the current state. Its primary function is to output the name of the next agent to invoke and the specific, self-contained task for that agent. Effective prompting requires clear instructions on how to interpret the state and follow the plan.  
  * **Example Prompt Fragment**: "You are a master orchestrator for a quantitative finance research team. Your goal is to execute the provided plan to fulfill the user's request. The overall user request is: '\[user\_request\]'. The current plan is: '\[plan\_json\]'. The working directory currently contains the following files: '\[file\_list\]'. The previous step, '\[last\_step\_description\]', was just completed. Based on the plan, determine the single next agent to invoke and formulate their task. Your output must be a JSON object with two keys: 'next\_agent' and 'task'."¹⁷

### **Planner Agent**

* **Role**: The Planner acts as the system's chief strategist. It takes the user's high-level, and often ambiguous, request and decomposes it into a detailed, sequential, and executable plan of action.¹³ This plan is the foundational document for the entire workflow, serving as the Orchestrator's script. The plan must be logical, feasible given the available tools, and structured in a machine-readable format like JSON.  
* **Prompting**: The Planner's prompt must be carefully engineered to encourage hierarchical thinking and structured output. It should be made explicitly aware of the full suite of tools available to the Executor agent, as the feasibility of the plan depends on the system's capabilities. Advanced prompting techniques such as Chain-of-Thought (CoT) or the more exhaustive Tree-of-Thought (ToT) are highly effective for this agent, as they encourage the model to reason through dependencies and potential roadblocks before finalizing the plan.²⁸  
  * **Example Prompt Fragment**: "You are an expert quantitative strategist and project planner. Your task is to create a detailed, step-by-step plan to address the following user request: '\[user\_request\]'. The available tools are: '\[list\_of\_tools\_with\_descriptions\]'. Break down the request into a logical sequence of discrete, actionable steps. Each step must be achievable with one or more of the available tools. Consider all necessary stages: data gathering, data analysis, strategy formulation, backtesting, and result synthesis. Output the plan as a JSON array, where each object in the array represents a step and contains 'step\_number', 'objective', and 'required\_tools' keys."

### **Executor Agent**

* **Role**: The Executor is the tactical "doer" of the system. It is a workhorse agent that receives a single, clearly defined task from the Orchestrator and executes it. It does not engage in high-level planning; its focus is on the immediate task at hand. This involves selecting the correct tool(s) from its available set, formulating the precise parameters for the tool call, executing the tool via the MCP, and interpreting the result.¹³ The ReAct loop is most active and critical for this agent, as it must handle potential tool errors, retry failed actions, or parse complex observations before reporting success or failure back to the Orchestrator.²  
* **Prompting**: The Executor's prompt is highly focused and action-oriented. It is given a single task and a list of available tools. The prompt must instruct the agent to think step-by-step to select the best tool and construct the correct arguments.  
  * **Example Task from Orchestrator**: "Download daily historical price data for SPY from January 1, 2020, to today and save it to a file named 'SPY\_data.csv'."  
  * **Executor's ReAct Process (Internal Monologue)**:  
    * **Thought**: The task is to download financial data. The finance\_data\_downloader tool is the most appropriate for this. It requires tickers, start\_date, and end\_date. The ticker is 'SPY', the start date is '2020-01-01', and the end date is today. I will call this tool.  
    * **Action**: finance\_data\_downloader(tickers=\['SPY'\], start\_date='2020-01-01', end\_date='2025-10-20')  
    * **Observation**: {"status": "success", "file\_path": "/requests/.../SPY\_data.csv"}  
    * **Thought**: The tool executed successfully and saved the data to 'SPY\_data.csv'. The task is complete. I will report success to the Orchestrator.

### **Writer & Report Generator Agent**

* **Role**: The Writer is the system's primary communicator. After all analytical tasks are completed, the Orchestrator delegates the final step to this agent. Its responsibility is to scan the entire working directory, ingest all relevant artifacts—data files, analysis results, performance metrics, and generated charts—and synthesize this information into a comprehensive, coherent, and human-readable report.²² The primary output format is Markdown for its flexibility and ease of conversion to other formats like PDF.  
* **Prompting**: The prompt for the Writer must emphasize synthesis and narrative construction. It should be instructed on the target audience (e.g., a portfolio manager, a risk committee), the desired structure of the report, and the tone (e.g., formal, analytical). It needs to be explicitly told to reference the files in the directory to ground its report in the generated data.  
  * **Example Prompt Fragment**: "You are an expert financial analyst and writer for a top-tier hedge fund. The working directory contains a complete analysis of a new trading strategy. Your task is to synthesize all findings into a professional investment memo in Markdown format. The files available are: '\[file\_list\]'. Structure your report with the following sections: 1\. Executive Summary, 2\. Strategy Hypothesis, 3\. Methodology and Data, 4\. Backtest Performance Analysis (referencing metrics from 'results\_final.json' and charts like 'equity\_curve.png'), 5\. Risk Assessment (focusing on drawdown from the results), and 6\. Final Recommendation. Ensure your writing is clear, concise, and data-driven."

### **The Strategy Refinement Team (Synthesizer, Evaluator, Judger)**

This sub-team of agents forms the core intellectual loop of the system, responsible for the iterative self-improvement of trading strategies.

* **Strategy Synthesizer**: This agent's role is to generate novel trading strategies in the form of executable Python code. It receives a high-level strategy concept or, in subsequent iterations, specific feedback from the Judger. Its prompts must be heavily engineered to produce code that is not only syntactically correct but also logically sound and adheres to the API of the backtesting library used in the sandbox.¹  
* **Strategy Evaluator**: This is a specialized instance of the Executor agent. Its sole task is to take the Python code generated by the Synthesizer, execute it within the secure sandbox using the python\_execution tool, run the backtest, and then use another tool to calculate a standard set of performance metrics. It saves these metrics to a structured JSON file (e.g., results\_iteration\_1.json) for the Judger to analyze.  
* **Judger/Critic**: This agent acts as the automated quality control and peer reviewer. It implements the "LLM-as-a-Judge" pattern, analyzing the performance metrics from the Evaluator against a predefined rubric of success.³⁰ Its most crucial function is to generate structured, actionable feedback that can guide the Synthesizer in the next iteration. The goal is not just to score the strategy but to provide concrete suggestions for improvement.³¹

The following table summarizes the key design parameters for each agent in the system.

| Agent Name | Persona | Core Responsibilities | Primary Tools Used | Key Prompting Strategy |
| :---- | :---- | :---- | :---- | :---- |
| **Master/Orchestrator** | System Project Manager | State tracking, task delegation, workflow control | file\_system\_scanner | Meta-level instructions focusing on routing and state. Provide plan and file list as context. Expect next agent name as output. |
| **Planner** | Expert Financial Analyst & Strategist | Decompose user goal into a detailed, step-by-step plan | None (pure reasoning) | Hierarchical decomposition. Use Chain-of-Thought. Provide list of available tools to ensure plan feasibility. Output structured JSON. |
| **Executor** | Tactical Doer / Analyst | Execute a single, specific task from the plan | All tools except file\_system\_scanner | Action-oriented, task-focused. Heavily relies on the ReAct loop to select tools, handle errors, and parse observations. |
| **Strategy Synthesizer** | Quantitative Developer | Generate executable Python code for trading strategies | file\_saver | Code generation focus. Provide clear requirements, backtesting library API docs, and iterative feedback from the Judger. |
| **Strategy Evaluator** | Backtesting Engine Operator | Execute strategy code in sandbox, compute performance metrics | python\_execution, regression\_based\_strategy\_evaluation | Specialized Executor. Follows a fixed sequence: execute code, calculate metrics, save results. |
| **Judger/Critic** | Head of Quantitative Research / Risk Manager | Evaluate backtest results, score strategy, provide actionable feedback | find\_in\_file | LLM-as-a-Judge pattern. Provide a clear, multi-faceted rubric (metrics, thresholds). Prompt for both a score and constructive, specific suggestions for improvement. |
| **Writer** | Financial Report Author | Synthesize all artifacts into a final, human-readable report | find\_in\_file, report\_generator | Narrative synthesis. Provide file list as context. Instruct on report structure, tone, and audience. Ground all claims in the available data. |

## **The Tooling Ecosystem: Data, Analysis, and Secure Execution**

The capabilities of the agentic system are fundamentally defined by the tools it can wield. These tools are the agents' hands and eyes, allowing them to interact with the external world to gather information, perform complex computations, and persist their work. This section details the design and implementation of the critical tools, with a particular focus on the secure execution of untrusted, LLM-generated code. All tools will expose an MCP-compliant interface.

### **Information Gathering Tools**

* **web\_search**: Serves as the agent's gateway to the internet. The DuckDuckGo search API is chosen for its simplicity and privacy features. The implementation will use a Python library like duckduckgo-search, exposing parameters like keywords, region, timelimit, and max\_results to the agent.³²  
* **find\_in\_web\_page / find\_in\_file**: Provide basic text-searching capabilities, such as finding keywords or using regular expressions to extract specific information from a file without loading its entire content into the context window.  
* **file\_saver**: A fundamental tool that takes a filename and content as input and writes the content to a file within the session's working directory.

### **Financial Data Tools**

* **finance\_data\_downloader**: The primary interface for fetching market data. The initial implementation will use the yfinance Python library.³³ Its function signature will be clearly defined, e.g., download(tickers: list\[str\], start\_date: str, end\_date: str, interval: str) \-\> str. It will save the data as a CSV and return the file path.³⁵  
* **Production Data Sources**: For a production-grade system, this tool would be re-implemented to connect to a commercial data provider like Bloomberg, Refinitiv, or Polygon.io. The MCP-compliant interface would remain the same.

### **Core Analytical Tools**

* **regression\_based\_strategy\_evaluation**: Provides a standardized method for evaluating a strategy's performance. It will take the time series of strategy returns and benchmark returns and perform a linear regression to calculate the strategy's **alpha** and **beta**.  
* **report\_generator**: Handles the final presentation of the report. It will take the path to the Markdown file generated by the Writer and convert it into a professionally formatted PDF document, likely using a backend tool like Pandoc.

### **Critical Infrastructure: The Secure Python Execution Sandbox**

Executing untrusted, LLM-generated code poses a significant security risk. A secure, isolated sandbox environment is an absolute necessity.²

Architectural Approach: Docker \+ Jupyter \+ FastAPI  
A robust architecture for a secure remote code execution environment involves³⁷:

1. **Docker**: Provides the foundational layer of process-level isolation from the host OS.³⁷  
2. **Jupyter Kernel**: A lightweight kernel provides a mature, stateful environment for executing Python code and capturing all outputs (text, errors, plots).³⁶  
3. **FastAPI**: A web framework wraps the Jupyter kernel and exposes its functionality through a secure RESTful API that agents interact with.³⁶

Enhanced Security with gVisor  
For a higher level of security, Docker containers can be run with gVisor. It creates a user-space kernel that intercepts and validates system calls, providing a strong barrier between the untrusted code and the host kernel.³⁶  
Managed Service Alternatives  
Alternatively, the system can integrate with managed sandbox services like Google Cloud's Vertex AI Code Execution³⁹ or E2B⁴⁰ to handle infrastructure, security, and scalability.  
Essential Sandbox Features  
The sandbox API must provide:

* **Stateful Sessions**: Variables and dataframes must persist between API calls within a session.³⁷  
* **Dependency Management**: All necessary libraries (pandas, numpy, scikit-learn, etc.) must be pre-installed via a Dockerfile.³⁷  
* **Resource Constraints**: Strict limits on CPU, memory, and execution time must be enforced.³⁷  
* **Filesystem Isolation**: The sandbox must only have access to the current request's working directory.  
* **Network Control**: Outbound network access should be disabled or heavily restricted.

The sandbox should be rigorously tested against potential exploits using frameworks like **SandboxEval** to probe for common vulnerabilities.⁴¹

The following table provides the definitive API specifications for the system's key tools.

| Tool Name | Description for LLM | MCP-Compliant API Definition (JSON Schema) | Primary Agent User(s) |
| :---- | :---- | :---- | :---- |
| **web\_search** | Searches the web using DuckDuckGo to find up-to-date information on a given topic. | {"name": "web\_search", "description": "...", "parameters": {"type": "object", "properties": {"keywords": {"type": "string"}, "timelimit": {"type": "string", "enum": \["d", "w", "m", "y"\]}}, "required": \["keywords"\]}} | Executor |
| **finance\_data\_downloader** | Downloads historical financial market data (OHLCV) for a list of stock tickers over a specified date range. | {"name": "finance\_data\_downloader", "description": "...", "parameters": {"type": "object", "properties": {"tickers": {"type": "array", "items": {"type": "string"}}, "start\_date": {"type": "string", "format": "date"}, "end\_date": {"type": "string", "format": "date"}}, "required": \["tickers", "start\_date", "end\_date"\]}} | Executor, Strategy Evaluator |
| **python\_execution** | Executes a block of Python code in a secure, stateful sandbox. Use this for data analysis, simulations, and backtesting. | {"name": "python\_execution", "description": "...", "parameters": {"type": "object", "properties": {"code": {"type": "string"}, "session\_id": {"type": "string"}}, "required": \["code", "session\_id"\]}} | Executor, Strategy Evaluator |
| **file\_saver** | Saves a given string of content to a file in the current working directory. | {"name": "file\_saver", "description": "...", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "content": {"type": "string"}}, "required": \["filename", "content"\]}} | Executor, Strategy Synthesizer |
| **file\_system\_scanner** | Scans the current working directory and returns a list of all files and their metadata. | {"name": "file\_system\_scanner", "description": "...", "parameters": {"type": "object", "properties": {}}} | Master/Orchestrator |

## **The Self-Improvement Cycle: Iterative Strategy Refinement**

The intellectual core of this system is its capacity for self-improvement through an iterative feedback loop involving the Strategy Synthesizer, Strategy Evaluator, and Judger/Critic. This loop mimics the scientific method: formulate a hypothesis (synthesis), run an experiment (evaluation), and analyze the results to inform the next hypothesis (judgment). The system is configured to run this cycle three times per request.

### **Workflow Overview: The Three-Cycle Loop**

1. **Iteration 1**:  
   * **Synthesis**: The **Strategy Synthesizer** generates strategy\_v1.py based on the user's request.  
   * **Evaluation**: The **Strategy Evaluator** executes the code, runs a backtest, and saves the performance metrics to results\_v1.json.  
   * **Judgment**: The **Judger/Critic** analyzes the metrics and generates actionable suggestions for improvement in feedback\_v1.txt. For instance: "Score: 4/10. The Sharpe ratio is \-0.5. The entry signals are too frequent, leading to excessive transaction costs. Suggestion: Modify the strategy to only take trades when the Bollinger Band width is above a certain threshold..."  
2. **Iteration 2**:  
   * **Synthesis (with Feedback)**: The **Strategy Synthesizer** is re-invoked with the original goal and the contents of feedback\_v1.txt, generating strategy\_v2.py.  
   * **Evaluation & Judgment**: The process repeats, producing results\_v2.json and feedback\_v2.txt.  
3. **Iteration 3**:  
   * The loop runs one final time, leveraging the feedback from the second iteration to produce strategy\_v3.py and results\_v3.json.

After the third iteration, the Orchestrator passes all artifacts to the Writer agent for final reporting.

### **Designing the Judger/Critic Agent**

The Judger/Critic is the most critical agent in the loop. It implements the **"LLM-as-a-Judge"** pattern to provide nuanced, qualitative assessments.³⁰ Designing it requires a formal, structured approach³¹:

1. **Defining the Rubric**: The Judger's prompt must contain a clear, multi-faceted rubric that defines a "good" strategy, developed by capturing feedback from human domain experts.  
2. **Establishing Ground Truth**: The Judger's prompts are calibrated against a small dataset of sample backtest results that have been manually scored by human experts to ensure its judgments align.  
3. **Generating Actionable Feedback**: The prompt must explicitly instruct the agent to explain *why* a strategy received a score and to provide *concrete, specific suggestions* for improvement.  
   * **Example Judger Prompt Fragment**: "You are the Head of Quantitative Research, acting as a critic. You will be given a JSON object containing the performance metrics of a backtested trading strategy. Your task is to evaluate this strategy based on the following rubric... First, provide a 'score' from 1 to 10\. Second, provide a 'critique' explaining your score. Third, provide actionable 'suggestions' for the next iteration. Your suggestions should be specific code or logic changes..."

### **The Evaluator's Toolkit: Key Performance Metrics**

The Judger's analysis is grounded in objective data produced by the Strategy Evaluator. The sandbox should use established backtesting libraries like Zipline or backtrader to calculate these metrics.⁴³

The definitive rubric for strategy evaluation is as follows:

| Metric Category | Metric Name | Definition | Industry Benchmark/Interpretation |
| :---- | :---- | :---- | :---- |
| **Profitability** | Annualized Return | The geometric average amount of money earned by an investment each year. | Should significantly outperform a passive market benchmark (e.g., S\&P 500 \~9-10%). |
| **Profitability** | Profit Factor | Gross Profits / Gross Losses | \> 1.0 is profitable. \> 1.75 is strong. \> 4.0 may indicate overfitting.⁴⁵ |
| **Risk-Adjusted Return** | Sharpe Ratio | $(R\_p \- R\_f) / \\sigma\_p$ | \< 1.0: Sub-optimal. 1.0–2.0: Good. \> 2.0: Very good.⁴⁵ |
| **Risk-Adjusted Return** | Sortino Ratio | $(R\_p \- R\_f) / \\sigma\_d$ (downside deviation) | Similar to Sharpe, focuses on "bad" volatility. \> 2.0 is generally strong.⁴⁵ |
| **Risk & Drawdown** | Maximum Drawdown (MDD) | The largest percentage drop from a portfolio's peak to its subsequent trough. | Highly dependent on risk tolerance. \< 15-20% is often desirable.⁴⁵ |
| **Risk & Drawdown** | Calmar Ratio | Annualized Return / Absolute Value of MDD | Measures return per unit of drawdown risk. \> 2.0 is often considered very good.⁴⁵ |
| **Trade Statistics** | Win Rate | (Number of Winning Trades / Total Number of Trades) \* 100 | Strategy-dependent. Not necessarily \>50% if reward/risk is high.⁴⁵ |
| **Trade Statistics** | Reward/Risk Ratio | Average Profit of Winning Trades / Average Loss of Losing Trades | \> 1.5 suggests profits on winning trades are substantially larger than losses.⁴⁸ |

## **Operational Considerations and Advanced Topics**

Deploying a complex, LLM-based system requires careful consideration of operational challenges.

### **Robustness and Error Handling**

* **Coordination Failures**: The Master/Orchestrator must handle failures gracefully with:  
  * **Timeouts**: To prevent the system from hanging on a non-responsive component.¹⁸  
  * **Retry Mechanisms**: With exponential backoff for transient errors like network issues.⁵⁰  
  * **Fallback and Escalation**: Rerunning the Planner or escalating to a human operator if a task repeatedly fails.⁵¹  
* **Cascading Failures**: Employ architectural patterns like the **Circuit Breaker** to prevent a failing component from destabilizing the entire system.⁵⁰  
* **Observability**: Comprehensive, structured logging is a core requirement. Every thought, action, and observation must be logged with rich context to a centralized platform like Datadog or New Relic for traceability and debugging.⁹

### **Economic Viability: Cost Optimization**

* **Intelligent Model Routing**: Use smaller, faster, cheaper models (e.g., Anthropic's Haiku) for simple tasks, reserving the most powerful models (e.g., Claude 3 Opus) for cognitively demanding tasks like planning (Planner) and critical analysis (Judger).²  
* **Semantic Caching**: Store and reuse responses for identical or semantically similar requests to bypass the expensive workflow, potentially reducing costs by 20-40%.⁵⁴  
* **Prompt Optimization**: Engineer prompts to be concise without sacrificing clarity to minimize token counts.⁵⁴  
* **Batch Processing**: For non-time-sensitive workloads, use batch API endpoints, which are often offered at a discount.⁵⁴

### **Future Enhancements: Advanced Planning and Generation**

* **Monte Carlo Tree Search (MCTS) for Planning**: For highly complex requests, the Planner could be enhanced with MCTS to more intelligently search the vast space of possible action sequences for an optimal plan.⁵⁶  
* **Hierarchical Planning for Report Generation**: The Writer could be improved with a hierarchical mechanism, first generating a high-level outline and then iteratively generating content for each section to ensure global coherence in long-form reports.⁵⁸

A truly mature system would introduce a "governance layer" or "meta-agent" that sits above the Master/Orchestrator. This layer would monitor the health and efficiency of the system itself (cost-per-request, error rates, latency) and make dynamic strategic decisions, such as adjusting the model routing policy or throttling requests to stay within a budget. This evolves the architecture from a two-level hierarchy (Orchestrator \-\> Workers) to a more sophisticated three-level one (Governance \-\> Orchestrator \-\> Workers).

## **Conclusion and Recommendations**

This report has detailed a comprehensive architecture for an autonomous multi-agent system for quantitative finance, synthesizing leading-edge AI paradigms to create a system that is powerful, robust, auditable, and extensible.

### **Summary of Architectural Decisions**

* **Supervisor-Worker Model**: Provides centralized control for predictability and traceability.  
* **ReAct Cognitive Framework**: Empowers agents to reason, act, and learn from observations, grounding logic in factual data.  
* **Model Context Protocol (MCP)**: Establishes a standardized and secure communication layer for agent-tool interactions.  
* **File-Based State Management**: Creates an inherently auditable and resilient system using the local file system as an external memory.  
* **Secure Execution Sandbox**: Isolates untrusted code execution, a critical security measure.  
* **Iterative Refinement Loop**: Implements an "LLM-as-a-Judge" feedback cycle for autonomous self-improvement.

### **Actionable Implementation Roadmap**

A phased, iterative implementation is recommended:

1. **Phase 1: Foundational Infrastructure and Tooling**: Build and validate the secure Python sandbox and core MCP-compliant tools.  
2. **Phase 2: Single-Agent Proof of Concept**: Validate the ReAct loop and tool integration with a single Executor agent and a hard-coded plan.  
3. **Phase 3: Core Multi-Agent System (MAS) Implementation**: Build the Master/Orchestrator and Planner to create the full supervisor-worker workflow.  
4. **Phase 4: The Intelligence Layer \- Strategy Refinement Loop**: Implement the Synthesizer, Evaluator, and Judger agents and integrate them into the three-cycle loop.  
5. **Phase 5: Productionization and Operational Hardening**: Implement comprehensive logging, robust error handling, cost optimization strategies, and a user interface.

Following this roadmap will allow a development team to systematically build and de-risk this complex system, culminating in a powerful, autonomous platform for quantitative finance research.

#### **Works Cited**

1. Automate Strategy Finding with LLM in Quant Investment \- arXiv, accessed October 20, 2025, https://arxiv.org/html/2409.06289v3  
2. What is a ReAct Agent? | IBM, accessed October 20, 2025, https://www.ibm.com/think/topics/react-agent  
3. ReACT Agent Model \- Klu.ai, accessed October 20, 2025, https://klu.ai/glossary/react-agent-model  
4. ReAct Prompting | Prompt Engineering Guide, accessed October 20, 2025, https://www.promptingguide.ai/techniques/react  
5. Building ReAct Agents from Scratch: A Hands-On Guide using Gemini \- Medium, accessed October 20, 2025, https://medium.com/google-cloud/building-react-agents-from-scratch-a-hands-on-guide-using-gemini-ffe4621d90ae  
6. Agent architectures, accessed October 20, 2025, https://langchain-ai.github.io/langgraphjs/concepts/agentic\_concepts/  
7. Agent architectures \- GitHub Pages, accessed October 20, 2025, https://langchain-ai.github.io/langgraph/concepts/agentic\_concepts/  
8. Multi-agent systems \- Overview, accessed October 20, 2025, https://langchain-ai.github.io/langgraph/concepts/multi\_agent/  
9. AI Agent Orchestration Patterns \- Azure Architecture Center \- Microsoft Learn, accessed October 20, 2025, https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns  
10. From RAG to Multi-Agent Systems: A Survey of Modern Approaches in LLM Development, accessed October 20, 2025, https://www.preprints.org/manuscript/202502.0406/v1  
11. What is AI Agent Orchestration? \- IBM, accessed October 20, 2025, https://www.ibm.com/think/topics/ai-agent-orchestration  
12. Large Language Model Based Multi- agents: A Survey of Progress and Challenges \- KAUST Repository, accessed October 20, 2025, https://repository.kaust.edu.sa/server/api/core/bitstreams/314fe81f-cfa1-4d93-8262-c1cde761c754/content  
13. Building Multi-Agent Architectures → Orchestrating Intelligent Agent Systems | by Akanksha Sinha | Medium, accessed October 20, 2025, https://medium.com/@akankshasinha247/building-multi-agent-architectures-orchestrating-intelligent-agent-systems-46700e50250b  
14. Multi-Agent Architecture – How Intelligent Systems Work Together \- Lyzr AI, accessed October 20, 2025, https://www.lyzr.ai/blog/multi-agent-architecture/  
15. What is Multi-Agent Orchestration? An Overview \- Talkdesk, accessed October 20, 2025, https://www.talkdesk.com/blog/multi-agent-orchestration/  
16. Building a Multi-Agent AI System for Financial Market Analysis \- Analytics Vidhya, accessed October 20, 2025, https://www.analyticsvidhya.com/blog/2025/02/financial-market-analysis-ai-agent/  
17. How we built our multi-agent research system \- Anthropic, accessed October 20, 2025, https://www.anthropic.com/engineering/multi-agent-research-system  
18. Multi-Agent Coordination Gone Wrong? Fix With 10 Strategies \- Galileo AI, accessed October 20, 2025, https://galileo.ai/blog/multi-agent-coordination-strategies  
19. Autono: A ReAct-Based Highly Robust Autonomous Agent Framework1footnote 11footnote 1Repo: https://github.com/vortezwohl/Autono \- arXiv, accessed October 20, 2025, https://arxiv.org/html/2504.04650v1  
20. What is A2A protocol (Agent2Agent)? \- IBM, accessed October 20, 2025, https://www.ibm.com/think/topics/agent2agent-protocol  
21. Autono: A ReAct-Based Highly Robust Autonomous Agent Framework, accessed October 20, 2025, https://arxiv.org/html/2504.04650  
22. Build an intelligent financial analysis agent with LangGraph and Strands Agents \- AWS, accessed October 20, 2025, https://aws.amazon.com/blogs/machine-learning/build-an-intelligent-financial-analysis-agent-with-langgraph-and-strands-agents/  
23. Top 5 Open Protocols for Building Multi-Agent AI Systems 2025 \- OneReach, accessed October 20, 2025, https://onereach.ai/blog/power-of-multi-agent-ai-open-protocols/  
24. Advancing Multi-Agent Systems Through Model Context Protocol: Architecture, Implementation, and Applications | by Eleventh Hour Enthusiast | Medium, accessed October 20, 2025, https://medium.com/@EleventhHourEnthusiast/advancing-multi-agent-systems-through-model-context-protocol-architecture-implementation-and-5146564bc1ff  
25. Effective context engineering for AI agents \- Anthropic, accessed October 20, 2025, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents  
26. How to Build Multi Agent AI Systems With Context Engineering \- Vellum AI, accessed October 20, 2025, https://www.vellum.ai/blog/multi-agent-systems-building-with-context-engineering  
27. Building Effective AI Agents \- Anthropic, accessed October 20, 2025, https://www.anthropic.com/research/building-effective-agents  
28. What is Prompt Engineering? \- AI Prompt Engineering Explained \- AWS, accessed October 20, 2025, https://aws.amazon.com/what-is/prompt-engineering/  
29. Build a powerful AI finance agent with Python \- PyQuant News, accessed October 20, 2025, https://www.pyquantnews.com/the-pyquant-newsletter/build-powerful-ai-finance-agent-python  
30. When AIs Judge AIs: The Rise of Agent-as-a-Judge Evaluation for LLMs \- arXiv, accessed October 20, 2025, https://arxiv.org/html/2508.02994v1  
31. From Human to Agentic Evaluation: Designing and Aligning The ..., accessed October 20, 2025, https://www.faktion.com/post/from-human-to-agentic-evaluation-designing-and-aligning-the-llm-as-a-judge-agent  
32. duckduckgo-search · PyPI, accessed October 20, 2025, https://pypi.org/project/duckduckgo-search/  
33. yfinance documentation \- GitHub Pages, accessed October 20, 2025, https://ranaroussi.github.io/yfinance/  
34. yfinance · PyPI, accessed October 20, 2025, https://pypi.org/project/yfinance/  
35. Yahoo Finance API \- A Complete Guide \- AlgoTrading101 Blog, accessed October 20, 2025, https://algotrading101.com/learn/yahoo-finance-api-guide/  
36. Setting Up a Secure Python Sandbox for LLM Agents, accessed October 20, 2025, https://dida.do/blog/setting-up-a-secure-python-sandbox-for-llm-agents  
37. Building a Sandboxed Environment for AI generated Code ..., accessed October 20, 2025, https://anukriti-ranjan.medium.com/building-a-sandboxed-environment-for-ai-generated-code-execution-e1351301268a  
38. typper-io/ai-code-sandbox: Secure Python sandbox for AI ... \- GitHub, accessed October 20, 2025, https://github.com/typper-io/ai-code-sandbox  
39. Introducing Code Execution: The code sandbox for your agents on Vertex AI Agent Engine, accessed October 20, 2025, https://discuss.google.dev/t/introducing-code-execution-the-code-sandbox-for-your-agents-on-vertex-ai-agent-engine/264336  
40. Secure code execution \- Hugging Face, accessed October 20, 2025, https://huggingface.co/docs/smolagents/v1.12.0/tutorials/secure\_code\_execution  
41. SandboxEval: Towards Securing Test Environment for Untrusted Code \- arXiv, accessed October 20, 2025, https://arxiv.org/html/2504.00018v1  
42. EvalPlanner: a Thinking-LLM-as-a-Judge model that learns to think by planning and reasoning for evaluation | by SACHIN KUMAR | Medium, accessed October 20, 2025, https://medium.com/@techsachin/evalplanner-a-thinking-llm-as-a-judge-model-that-learns-to-think-by-planning-and-reasoning-for-b7537822970d  
43. Python Libraries for Quantitative Trading | QuantStart, accessed October 20, 2025, https://www.quantstart.com/articles/python-libraries-for-quantitative-trading/  
44. QuantRocket \- Data-Driven Trading with Python, accessed October 20, 2025, https://www.quantrocket.com/  
45. Top 7 Metrics for Backtesting Results \- LuxAlgo, accessed October 20, 2025, https://www.luxalgo.com/blog/top-7-metrics-for-backtesting-results/  
46. Essential Backtesting Metrics in Algo Trading, accessed October 20, 2025, https://www.utradealgos.com/blog/what-are-the-key-metrics-to-track-in-algo-trading-backtesting  
47. Backtesting Trading Strategies: A Complete Guide to Success, accessed October 20, 2025, https://tradewiththepros.com/backtesting-trading-strategies/  
48. Backtesting Key Performance Indicators (KPIs) | TrendSpider Learning Center, accessed October 20, 2025, https://trendspider.com/learning-center/backtesting-key-performance-indicators-kpis/  
49. How do multi-agent systems handle coordination failures? \- Zilliz Vector Database, accessed October 20, 2025, https://zilliz.com/ai-faq/how-do-multiagent-systems-handle-coordination-failures  
50. Error Handling Strategies: 7 Smart Fixes for Success \- GO-Globe, accessed October 20, 2025, https://www.go-globe.com/error-handling-strategies-7-smart-fixes  
51. How can I be 100% sure that my AI Agent will not fail in production? Any process or industry practice : r/AI\_Agents \- Reddit, accessed October 20, 2025, https://www.reddit.com/r/AI\_Agents/comments/1k7iunr/how\_can\_i\_be\_100\_sure\_that\_my\_ai\_agent\_will\_not/  
52. 5 Steps to Build Exception Handling for AI Agent Failures | Datagrid, accessed October 20, 2025, https://www.datagrid.com/blog/exception-handling-frameworks-ai-agents  
53. Why Multi-Agent Systems Need Memory Engineering | MongoDB \- Medium, accessed October 20, 2025, https://medium.com/mongodb/why-multi-agent-systems-need-memory-engineering-153a81f8d5be  
54. The Complete Guide to Reducing LLM Costs Without Sacrificing Quality \- DEV Community, accessed October 20, 2025, https://dev.to/kuldeep\_paul/the-complete-guide-to-reducing-llm-costs-without-sacrificing-quality-4gp3  
55. How to Reduce LLM Costs: 10 Proven Strategies for Budget-Friendly AI \- Uptech, accessed October 20, 2025, https://www.uptech.team/blog/how-to-reduce-llm-costs  
56. Monte Carlo Tree Search: A Guide | Built In, accessed October 20, 2025, https://builtin.com/machine-learning/monte-carlo-tree-search  
57. Improving Text Generation Quality with Monte Carlo Tree Search (MCTS) in Retrieval Augmented… \- Medium, accessed October 20, 2025, https://medium.com/@ari\_in\_media\_res/improving-text-quality-with-monte-carlo-tree-search-mcts-in-retrieval-augmented-generation-59e9c14cda4a  
58. Agent Communication Patterns: Beyond Single Agent Responses ..., accessed October 20, 2025, https://agenticlab.digital/agent-communication-patterns-beyond-single-agent-responses/  
59. Efficient Multi-Agent System Training with Data Influence-Oriented Tree Search \- arXiv, accessed October 20, 2025, https://arxiv.org/html/2502.00955v1  
60. Monte Carlo Tree Search for Code Generation using LLMs \- Arun Patro, accessed October 20, 2025, https://arunpatro.github.io/blog/mcts/  
61. Hierarchical Sampling-based Planner with LTL Constraints and Text Prompting \- arXiv, accessed October 20, 2025, https://arxiv.org/html/2501.06719v1  
62. Hierarchical Text Generation and Planning for Strategic Dialogue \- Proceedings of Machine Learning Research, accessed October 20, 2025, https://proceedings.mlr.press/v80/yarats18a/yarats18a.pdf  
63. Long and Diverse Text Generation with Planning-based Hierarchical Variational Model, accessed October 20, 2025, https://aclanthology.org/D19-1321/  
64. A Hierarchical Model for Data-to-Text Generation \- PMC, accessed October 20, 2025, https://pmc.ncbi.nlm.nih.gov/articles/PMC7148215/