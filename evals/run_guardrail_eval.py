import json
import asyncio
from pathlib import Path
from agents import Runner
from agent_sdk.guardrails import claim_checker
from agent_sdk.tools import DEMO_FILE
from dotenv import load_dotenv
load_dotenv()



async def main():
    CASES_FILE = Path(__file__).resolve().parent/ "guardrail_cases.json"
    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))

    facts = DEMO_FILE.read_text(encoding="utf-8")

    passed_count = 0
    false_positives = 0
    false_negatives = 0

    for case in cases:
        judge_input = f"RESUME FACTS:\n{facts}\n\nDRAFTED NOTE:\n{case['note']}"

        result = await Runner.run(claim_checker, judge_input)
        verdict = result.final_output

        actual = "blocked" if verdict.has_unsupported_claims else "clean"
        passed = (actual == case["expected"])

        status = "PASS" if passed else "FAIL"

        print(
            f"{case['id']} | Expected: {case['expected']} | "
            f"Actual: {actual} | {status}")

        if passed:
            passed_count+=1
        else:
            if case["expected"] == "clean" and actual =="blocked":
                false_positives+=1
            elif case["expected"] == "blocked" and actual=="clean":
                false_negatives+=1

            print(f"Reasoning: {verdict.reasoning}")

    print("\n--- Guardrail Test Summary ---")
    print(f"Passed: {passed_count}/{len(cases)}")
    print(f"False Positives: {false_positives}")
    print(f"False Negatives: {false_negatives}")


if __name__ == "__main__":
    asyncio.run(main())

    



