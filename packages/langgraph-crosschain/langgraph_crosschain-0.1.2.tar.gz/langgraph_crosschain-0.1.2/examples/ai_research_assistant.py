"""
AI Research Assistant - Multi-Chain Workflow Example

This demonstrates a real-world multi-chain workflow where specialized
chains collaborate to research a topic and generate a comprehensive report.

Architecture:
    User Query → Researcher → Analyzer → Writer → Quality Check → Final Report
                 (Chain1)     (Chain2)   (Chain3)   (Chain4)

Key Concepts Demonstrated:
    - Sequential workflow execution
    - Shared state coordination
    - Specialized chain responsibilities
    - Quality assurance patterns
    - Production-ready structure
"""

from typing import Any

from langgraph.graph import END, StateGraph

from langgraph_crosschain import (
    ChainRegistry,
    SharedStateManager,
    get_logger,
)

# Set up logging
logger = get_logger(__name__)


# Define state type
class State(dict[str, Any]):
    """State type for all chains."""

    pass


# ============================================================================
# STEP 1: Research Chain - Gathers information
# ============================================================================


def research_query(state: State) -> State:
    """Research the given topic and gather information."""
    print("\n" + "=" * 70)
    print("🔍 RESEARCH CHAIN: Starting research...")
    print("=" * 70)

    topic = state.get("topic", "")
    print(f"Topic: {topic}")

    # In a real application, this would:
    # - Query a vector database
    # - Call web search APIs
    # - Retrieve documents from a knowledge base
    # - Use RAG (Retrieval Augmented Generation)

    # Simulated research results
    research_results = {
        "topic": topic,
        "sources": [
            {
                "title": f"Introduction to {topic}",
                "content": f"Key concepts and fundamentals of {topic}...",
                "relevance": 0.95,
                "url": f"https://example.com/{topic.lower().replace(' ', '-')}-intro",
            },
            {
                "title": f"Advanced {topic} Techniques",
                "content": f"Advanced methods and best practices for {topic}...",
                "relevance": 0.88,
                "url": f"https://example.com/{topic.lower().replace(' ', '-')}-advanced",
            },
            {
                "title": f"{topic} Case Studies",
                "content": f"Real-world applications and examples of {topic}...",
                "relevance": 0.82,
                "url": f"https://example.com/{topic.lower().replace(' ', '-')}-cases",
            },
        ],
        "key_findings": [
            f"{topic} is widely used in modern applications",
            f"Best practices for {topic} include systematic approaches",
            f"Common challenges with {topic} involve scalability and implementation",
        ],
    }

    # Store in shared state for other chains
    manager = SharedStateManager()
    manager.set("research_results", research_results)

    print(f"✓ Found {len(research_results['sources'])} sources")
    print(f"✓ Identified {len(research_results['key_findings'])} key findings")

    state["research_complete"] = True
    return state


def create_research_chain():
    """Create the research chain."""
    workflow = StateGraph(State)
    workflow.add_node("research", research_query)
    workflow.set_entry_point("research")
    workflow.add_edge("research", END)
    return workflow.compile()


# ============================================================================
# STEP 2: Analysis Chain - Analyzes the research
# ============================================================================


def analyze_results(state: State) -> State:
    """Analyze the research results and extract insights."""
    print("\n" + "=" * 70)
    print("📊 ANALYSIS CHAIN: Analyzing research results...")
    print("=" * 70)

    manager = SharedStateManager()
    research = manager.get("research_results")

    if not research:
        print("❌ No research results found!")
        state["analysis_complete"] = False
        return state

    # In a real application, this would:
    # - Use an LLM to analyze findings
    # - Identify patterns and connections
    # - Score relevance and quality
    # - Extract key themes and insights

    # Calculate average relevance
    avg_relevance = sum(s["relevance"] for s in research["sources"]) / len(research["sources"])

    analysis = {
        "topic": research["topic"],
        "insights": [
            f"Primary insight: {research['topic']} is essential for modern technology stacks",
            "Secondary insight: Most sources agree that proper implementation is crucial",
            f"Key recommendation: When implementing {research['topic']}, start with fundamentals",
        ],
        "themes": ["fundamentals", "best practices", "real-world usage"],
        "confidence_score": avg_relevance,
        "source_quality": "high" if avg_relevance > 0.85 else "medium",
        "citations_needed": len(research["sources"]),
    }

    # Store analysis
    manager.set("analysis_results", analysis)

    print(f"✓ Generated {len(analysis['insights'])} insights")
    print(f"✓ Identified {len(analysis['themes'])} themes")
    print(f"✓ Confidence score: {analysis['confidence_score']:.2%}")
    print(f"✓ Source quality: {analysis['source_quality']}")

    state["analysis_complete"] = True
    return state


def create_analysis_chain():
    """Create the analysis chain."""
    workflow = StateGraph(State)
    workflow.add_node("analyze", analyze_results)
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", END)
    return workflow.compile()


# ============================================================================
# STEP 3: Writer Chain - Generates the report
# ============================================================================


def write_report(state: State) -> State:
    """Generate a comprehensive report from the analysis."""
    print("\n" + "=" * 70)
    print("✍️  WRITER CHAIN: Writing report...")
    print("=" * 70)

    manager = SharedStateManager()
    research = manager.get("research_results")
    analysis = manager.get("analysis_results")

    if not research or not analysis:
        print("❌ Missing research or analysis!")
        state["writing_complete"] = False
        return state

    # In a real application, this would:
    # - Use an LLM to generate prose (GPT-4, Claude, etc.)
    # - Format citations properly
    # - Create structured sections
    # - Generate executive summary

    report = {
        "title": f"Research Report: {research['topic']}",
        "sections": [
            {
                "heading": "Executive Summary",
                "content": (
                    f"This report examines {research['topic']} based on "
                    f"{len(research['sources'])} authoritative sources with an average "
                    f"relevance score of {analysis['confidence_score']:.2%}. "
                    f"Our analysis identified {len(analysis['themes'])} key themes and "
                    f"generated {len(analysis['insights'])} actionable insights."
                ),
            },
            {
                "heading": "Key Findings",
                "content": "\n".join([f"• {finding}" for finding in research["key_findings"]]),
            },
            {
                "heading": "Detailed Analysis",
                "content": "\n".join([f"• {insight}" for insight in analysis["insights"]]),
            },
            {
                "heading": "Recommendations",
                "content": (
                    f"Based on our analysis with {analysis['confidence_score']:.0%} confidence, "
                    f"we recommend a phased approach to implementing {research['topic']}. "
                    f"The identified themes of {', '.join(analysis['themes'])} should guide "
                    f"your implementation strategy."
                ),
            },
            {
                "heading": "References",
                "content": "\n".join(
                    [
                        f"[{i+1}] {source['title']} - {source['url']}"
                        for i, source in enumerate(research["sources"])
                    ]
                ),
            },
        ],
        "word_count": 1250,
        "references": len(research["sources"]),
        "created_at": "2025-11-04",
    }

    # Store report
    manager.set("draft_report", report)

    print(f"✓ Generated report with {len(report['sections'])} sections")
    print(f"✓ Word count: {report['word_count']}")
    print(f"✓ References: {report['references']}")

    state["writing_complete"] = True
    return state


def create_writer_chain():
    """Create the writer chain."""
    workflow = StateGraph(State)
    workflow.add_node("write", write_report)
    workflow.set_entry_point("write")
    workflow.add_edge("write", END)
    return workflow.compile()


# ============================================================================
# STEP 4: Quality Check Chain - Reviews the report
# ============================================================================


def quality_check(state: State) -> State:
    """Perform quality checks on the generated report."""
    print("\n" + "=" * 70)
    print("✅ QUALITY CHECK CHAIN: Reviewing report...")
    print("=" * 70)

    manager = SharedStateManager()
    report = manager.get("draft_report")

    if not report:
        print("❌ No report to review!")
        state["quality_check_complete"] = False
        return state

    # In a real application, this would:
    # - Check for factual accuracy
    # - Verify citations
    # - Assess readability (Flesch-Kincaid, etc.)
    # - Check grammar and style
    # - Verify all sections are complete

    # Perform checks
    checks = {}

    # Check 1: Accuracy (has references?)
    checks["accuracy"] = {
        "score": 0.95 if report.get("references", 0) >= 3 else 0.70,
        "status": "pass" if report.get("references", 0) >= 3 else "warning",
    }

    # Check 2: Completeness (has all sections?)
    expected_sections = [
        "Executive Summary",
        "Key Findings",
        "Detailed Analysis",
        "Recommendations",
        "References",
    ]
    section_headings = [s["heading"] for s in report.get("sections", [])]
    has_all_sections = all(section in section_headings for section in expected_sections)
    checks["completeness"] = {
        "score": 0.90 if has_all_sections else 0.60,
        "status": "pass" if has_all_sections else "fail",
    }

    # Check 3: Clarity (word count reasonable?)
    word_count = report.get("word_count", 0)
    checks["clarity"] = {
        "score": 0.88 if 1000 <= word_count <= 3000 else 0.65,
        "status": "pass" if 1000 <= word_count <= 3000 else "warning",
    }

    # Check 4: Citations (references present?)
    checks["citations"] = {
        "score": 0.94 if "References" in section_headings else 0.50,
        "status": "pass" if "References" in section_headings else "fail",
    }

    # Calculate overall score
    overall_score = sum(check["score"] for check in checks.values()) / len(checks)

    # Determine approval
    approved = overall_score >= 0.80 and all(check["status"] != "fail" for check in checks.values())

    issues_found = sum(1 for check in checks.values() if check["status"] != "pass")

    quality_results = {
        "overall_score": overall_score,
        "checks": checks,
        "issues_found": issues_found,
        "approved": approved,
    }

    # Store quality results
    manager.set("quality_results", quality_results)

    # If approved, mark report as final
    if quality_results["approved"]:
        manager.set("final_report", report)
        print("✓ Report APPROVED for publication")
    else:
        print("⚠️  Report needs revisions")
        print(f"   Issues: {issues_found}")
        for check_name, check_data in checks.items():
            if check_data["status"] != "pass":
                print(
                    f"   - {check_name}: {check_data['status']} (score: {check_data['score']:.2f})"
                )

    print(f"✓ Overall quality score: {quality_results['overall_score']:.2%}")
    print(f"✓ Issues found: {quality_results['issues_found']}")

    state["quality_check_complete"] = True
    state["report_approved"] = quality_results["approved"]
    return state


def create_quality_chain():
    """Create the quality check chain."""
    workflow = StateGraph(State)
    workflow.add_node("quality_check", quality_check)
    workflow.set_entry_point("quality_check")
    workflow.add_edge("quality_check", END)
    return workflow.compile()


# ============================================================================
# ORCHESTRATOR: Coordinates the entire workflow
# ============================================================================


def run_research_workflow(topic: str) -> dict[str, Any]:
    """
    Run the complete research workflow.

    Args:
        topic: The research topic

    Returns:
        Final report and metadata

    Example:
        >>> result = run_research_workflow("Machine Learning")
        >>> print(result["final_report"]["title"])
        Research Report: Machine Learning
    """
    print("\n" + "🚀 " * 35)
    print("AI RESEARCH ASSISTANT - Multi-Chain Workflow")
    print("🚀 " * 35)
    print(f"\nResearching topic: '{topic}'\n")

    # Create registry and state manager
    registry = ChainRegistry()
    manager = SharedStateManager()

    # Clear previous state
    manager.clear()

    # Create and register all chains
    research_chain = create_research_chain()
    analysis_chain = create_analysis_chain()
    writer_chain = create_writer_chain()
    quality_chain = create_quality_chain()

    registry.register("researcher", research_chain)
    registry.register("analyzer", analysis_chain)
    registry.register("writer", writer_chain)
    registry.register("quality", quality_chain)

    print(f"✓ Registered {len(registry.list_chains())} specialized chains\n")

    # Execute workflow sequentially
    initial_state = {"topic": topic}

    try:
        # Step 1: Research
        print("Stage 1/4: Research Phase")
        research_result = research_chain.invoke(initial_state)

        # Step 2: Analysis
        print("\nStage 2/4: Analysis Phase")
        analysis_result = analysis_chain.invoke({})

        # Step 3: Writing
        print("\nStage 3/4: Writing Phase")
        writing_result = writer_chain.invoke({})

        # Step 4: Quality Check
        print("\nStage 4/4: Quality Assurance Phase")
        quality_result = quality_chain.invoke({})

    except Exception as e:
        print(f"\n❌ Error in workflow: {e}")
        logger.error(f"Workflow failed: {e}")
        return {"error": str(e)}

    # Collect final results
    final_state = manager.snapshot()

    # Display final report
    print("\n" + "=" * 70)
    print("📄 FINAL REPORT")
    print("=" * 70)

    final_report = final_state.get("final_report")
    if final_report:
        print(f"\nTitle: {final_report['title']}")
        print(f"Sections: {len(final_report['sections'])}")
        print(f"Word Count: {final_report['word_count']}")
        print(f"References: {final_report['references']}")
        print(f"Created: {final_report.get('created_at', 'N/A')}")

        print("\n--- Report Content ---\n")
        for section in final_report["sections"]:
            print(f"\n## {section['heading']}")
            print("-" * len(section["heading"]))
            content = section["content"]
            # Print first 300 chars of each section
            if len(content) > 300:
                print(content[:300] + "...\n[Content truncated]")
            else:
                print(content)
    else:
        print("⚠️  No final report available - quality check may have failed")

    # Display workflow summary
    print("\n" + "=" * 70)
    print("📊 WORKFLOW SUMMARY")
    print("=" * 70)
    quality_results = final_state.get("quality_results", {})

    # Check results (may be None due to LangGraph behavior)
    research_complete = research_result.get("research_complete", False) if research_result else True
    analysis_complete = analysis_result.get("analysis_complete", False) if analysis_result else True
    writing_complete = writing_result.get("writing_complete", False) if writing_result else True
    quality_complete = (
        quality_result.get("quality_check_complete", False) if quality_result else True
    )
    report_approved = (
        quality_result.get("report_approved", False)
        if quality_result
        else quality_results.get("approved", False)
    )

    print(f"✓ Research completed: {research_complete}")
    print(f"✓ Analysis completed: {analysis_complete}")
    print(f"✓ Writing completed: {writing_complete}")
    print(f"✓ Quality check completed: {quality_complete}")
    print(f"✓ Report approved: {report_approved}")
    if quality_results:
        print(f"✓ Quality score: {quality_results['overall_score']:.2%}")
        print(f"✓ Issues found: {quality_results['issues_found']}")

    # Display chain statistics
    print("\n" + "=" * 70)
    print("🔧 CHAIN STATISTICS")
    print("=" * 70)
    print(f"Total chains used: {len(registry.list_chains())}")
    print(f"Chains: {', '.join(registry.list_chains())}")
    print(f"Shared state keys: {len(manager.keys())}")
    print(f"State keys: {', '.join(manager.keys())}")

    print("\n" + "🎉 " * 35)
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("🎉 " * 35 + "\n")

    return final_state


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Run the AI research assistant with example topics."""

    # Example: Run a single research workflow
    print("\n" + "=" * 70)
    print("AI RESEARCH ASSISTANT DEMO")
    print("=" * 70)

    # You can change the topic here
    topic = "Machine Learning"

    result = run_research_workflow(topic)

    # Show what was generated
    if result.get("final_report"):
        print("\n" + "=" * 70)
        print("✅ SUCCESS - Report Generated!")
        print("=" * 70)
        print(f"\nYou can now use the generated report from the '{topic}' research.")
        print(f"The report has {result['final_report']['word_count']} words")
        print(f"and {result['final_report']['references']} references.")

        # Uncomment to try other topics:
        # result = run_research_workflow("Quantum Computing")
        # result = run_research_workflow("Climate Change")
        # result = run_research_workflow("Blockchain Technology")

    else:
        print("\n⚠️  Warning: No final report was generated")

    print("\n✅ Demo completed!\n")


if __name__ == "__main__":
    main()
