# mermaid_flow/cli.py
import os, sys, logging
from pathlib import Path
import argparse
from langchain_openai import ChatOpenAI
from core.common_types import DiagramType, Diagram_ManagerState
from core.utils import generate_context, clear_cache, generate_context_all
from mermaid_agent import build_diagram_agent

logger = logging.getLogger(__name__)

def create_diagram(llm, prompt, diagram_type, description="", output_file=None):
    agent = build_diagram_agent()
    state = Diagram_ManagerState(
        user_prompt=prompt,
        diagram_type=diagram_type,
        description=description,
        llm=llm
    )
    result = agent.invoke(state)

    mermaid_code = result["mermaid_code"]  # ή result.mermaid_code αν είναι pydantic
    print("\n" + "="*80)
    print("Generated Mermaid Diagram:")
    print("="*80)
    print(mermaid_code)
    print("="*80)

    validation = result["validation_result"]
    ok = bool(validation.get("valid"))
    print("✅ Validation: PASSED" if ok else "❌ Validation: FAILED")

    if validation.get("errors"):
        print("\nErrors:")
        for e in validation["errors"]:
            print(f"  - {e}")

    if validation.get("warnings"):
        print("\nWarnings:")
        for w in validation["warnings"]:
            print(f"  ⚠️  {w}")

    print(f"\nIterations: {result['iteration_count']}/{result['max_iterations']}")

    if result.get("errors"):
        print("\nSystem Errors:")
        for e in result["errors"]:
            print(f"  ❌ {e}")

    if output_file:
        p = Path(output_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(mermaid_code, encoding="utf-8")
        print(f"\n💾 Diagram saved to: {p}")

    print("\n🌐 Visualize at: https://mermaid.live/")
    return 0 if ok else 2  # μη-μηδενικό αν αποτύχει validation

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="Mermaid Diagram Manager")
    g = parser.add_argument_group("Diagram Creation")
    g.add_argument("--create", type=str, metavar="PROMPT")
    g.add_argument("--type", type=str, choices=[d.value for d in DiagramType], default="flowchart")
    g.add_argument("--description", type=str, default="")
    g.add_argument("-o", "--output", type=str)

    t = parser.add_argument_group("Template Management")
    t.add_argument("--generate-all", action="store_true")
    t.add_argument("--generate", type=str, choices=[d.value for d in DiagramType])
    t.add_argument("--clear", action="store_true")
    t.add_argument("--clear-type", type=str, choices=[d.value for d in DiagramType])

    l = parser.add_argument_group("LLM Configuration")
    l.add_argument("--use-openai", action="store_true")
    l.add_argument("--model", type=str)
    l.add_argument("--base-url", type=str, default=os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1"))
    l.add_argument("--api-key", type=str, default=os.getenv("OPENAI_API_KEY"))

    args = parser.parse_args()

    # init llm
    if args.use_openai:
        llm = ChatOpenAI(model=args.model or "gpt-4o-mini", temperature=0, api_key=args.api_key)
        logger.info("Using OpenAI API.")
    else:
        llm = ChatOpenAI(model=args.model or "deepseek-coder-v2-lite-instruct",
                         base_url=args.base_url, api_key=args.api_key or "EMPTY", temperature=0)
        logger.info(f"Using local LLM at {args.base_url}.")

    if args.create:
        code = create_diagram(llm, args.create, args.type, args.description, args.output)
        sys.exit(code)
    if args.clear:
        clear_cache(); sys.exit(0)
    if args.clear_type:
        dt = next(d for d in DiagramType if d.value == args.clear_type)
        clear_cache(dt); sys.exit(0)
    if args.generate_all:
        generate_context_all(llm); sys.exit(0)
    if args.generate:
        dt = next(d for d in DiagramType if d.value == args.generate)
        generate_context(llm, dt); sys.exit(0)

    parser.print_help()

if __name__ == "__main__":
    main()
