import os
import sys

from dotenv import load_dotenv

# Προσθέτουμε το root directory στο path για να βρίσκει τα modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent import EnterpriseAgentManager

load_dotenv()

#πιο απλοικα test cases 
TEST_CASES = [
    # {
    #     "id": 9,
    #     "category": "Excel Simple Lookup (Computed Cell)",
    #     "question": "What is the total FY2026 revenue in the annual budget?",
    #     "expected_answer": "$71,002,600 (about $71.0 million), shown as the FY2026 total on the Revenue Forecast and P&L Summary sheets."
    # },
    # {
    #     "id": 10,
    #     "category": "Excel Simple Lookup (Input Cell)",
    #     "question": "What corporate income tax rate is assumed in the FY2026 budget?",
    #     "expected_answer": "21%, applied to positive earnings before tax only (Assumptions sheet)."
    # },
    # {
    #     "id": 11,
    #     "category": "PowerPoint Simple Lookup (Table)",
    #     "question": "Who owns the EMEA market entry (Dublin hub) initiative and when is its go-live?",
    #     "expected_answer": "The owner is the COO and the go-live is Q3 2026 (the Dublin hub opens in August 2026). The initiative has an investment of $1,500K."
    # },
    {
        "id": 12,
        "category": "PowerPoint Simple Lookup (Text)",
        "question": "When is the portfolio kickoff in the Strategic Growth Plan 2026?",
        "expected_answer": "January 15, 2026, with all five initiative owners."
    }
    # {
    #     "id": 13,
    #     "category": "Markdown Simple Lookup (Table)",
    #     "question": "What are the RTO and RPO for a Tier 1 workload?",
    #     "expected_answer": "RTO is 15 minutes and RPO is 5 minutes. Tier 1 also requires an active-active pattern across two regions and a 99.99% availability SLO."
    # },
    # {
    #     "id": 14,
    #     "category": "Markdown Simple Lookup (Text)",
    #     "question": "How long must security and audit logs be retained?",
    #     "expected_answer": "400 days, of which the most recent 90 days must be immediately searchable."
    # },
    # {
    #     "id": 15,
    #     "category": "PDF Simple Lookup (Table)",
    #     "question": "What was the net income in Q3 2025?",
    #     "expected_answer": "$717 thousand (US$ 717K), compared with $190K in Q3 2024."
    # },
    # {
    #     "id": 16,
    #     "category": "PDF Simple Lookup (Text)",
    #     "question": "What revenue does management expect for Q4 2025?",
    #     "expected_answer": "Revenue of $16.0 million to $16.4 million, with an EBITDA margin of 9% to 10%."
    # },
]


#δυσκολα test cases 
# TEST_CASES = [
#     {
#         "id": 1,
#         "category": "Excel Multi-Sheet Calculation (Product Profitability)",
#         "question": "In the FY2026 budget, compare Meridian Analytics Suite and Meridian Edge Gateway on profitability. Which one earns more contribution margin per revenue dollar and which one earns more per unit sold, and what are the figures? Contribution margin is revenue minus COGS minus sales commissions.",
#         "expected_answer": "Analytics Suite earns more per revenue dollar: contribution margin of 64.0% (FY2026 contribution margin $16,551,936 on revenue $25,862,400). Edge Gateway earns more per unit: $975 per unit (contribution margin $6,591,000 on 6,760 units), compared with $768 per unit for Analytics Suite (21,552 units). Edge Gateway's contribution margin percentage is only 39.0%, the lowest of the three products (Secure Vault is 55.0% and $495 per unit)."
#     },
#     {
#         "id": 2,
#         "category": "Excel Scenario & Break-even Analysis",
#         "question": "What is the FY2026 EBITDA break-even revenue, and under the downside scenario, what are revenue, EBITDA and EBITDA margin? Does the downside revenue stay above break-even?",
#         "expected_answer": "EBITDA break-even revenue is about $55.27 million ($55,267,220), based on fixed OpEx excluding commissions of $30,104,000 and a blended contribution margin of 54.5%. Base-case revenue is $71,002,600, so the margin of safety is about 22.2%. In the downside scenario (revenue -10%), revenue is $63,902,340, EBITDA is about $4,703,541 and EBITDA margin is about 7.4% (the base case is $8,571,046 EBITDA at 12.1%). Yes, downside revenue stays above break-even by roughly $8.6 million."
#     },
#     {
#         "id": 3,
#         "category": "PowerPoint Table Calculation (Investment Portfolio ROI)",
#         "question": "In the Strategic Growth Plan 2026, which of the five initiatives has the highest 2-year ROI, what is it, and what is the overall 2-year ROI of the whole portfolio? Use the slide's definition: ROI = (2026 benefit + 2027 benefit - investment) / investment. Also, which initiative does not pay back within two years?",
#         "expected_answer": "Managed Support bundle attach program has the highest 2-year ROI: (300 + 500 - 250) / 250 = 220.0%. The total portfolio ROI is (1,910 + 5,360 - 4,300) / 4,300 = 2,970 / 4,300, about 69.1%. DataVault storage-tier optimization does not pay back within two years: cumulative benefit of $670K (130 + 540) against $900K invested, a 2-year ROI of about -25.6%."
#     },
#     {
#         "id": 4,
#         "category": "PowerPoint Chart Data & Calculation (Revenue by Product Line)",
#         "question": "According to the Strategic Growth Plan 2026 revenue chart, which product line adds the most revenue in absolute dollars in FY2026, by how much and at what growth rate? And what share of total FY2026 revenue does Insight Analytics represent?",
#         "expected_answer": "CloudSync Pro adds the most in absolute terms: +$1,890K (from $10,500K to $12,390K, +18%). Insight Analytics has the highest growth rate (+35%) but a smaller absolute increase of $1,470K. Insight Analytics FY2026 revenue is $5,670K out of a total of $31,292K, which is about 18.1% of total revenue."
#     },
#     {
#         "id": 5,
#         "category": "Markdown Policy Reasoning (Approvals, Security & DR)",
#         "question": "A team wants to migrate a Tier 2 workload that stores Restricted customer data for an EU customer. The estimated steady-state cost is $60,000 per month. Which approvals are required, which regions are allowed, what encryption and key requirements apply, and what DR pattern, RTO and RPO are required?",
#         "expected_answer": "Approvals: at $60,000 per month (the $50,001-$150,000 band) the workload needs Engineering Manager approval, CCoE review and ARB approval; CFO sign-off is not needed because the cost is below $150,000. Because it handles Restricted data, a Security Architecture review by Information Security is also required regardless of cost. Regions: only the customer's contractual home region, so EU data stays in the EU (eu-west-1 Ireland or eu-central-1 Frankfurt). Encryption: AES-256 with HSM-backed keys, TLS 1.3 with mutual TLS (mTLS) between services, and customer-managed keys rotated every 90 days. DR: Tier 2 requires a warm standby in a second region (which, for EU data, must also be an EU region), with RTO of 2 hours, RPO of 30 minutes and a 99.95% availability SLO."
#     },
#     {
#         "id": 6,
#         "category": "Markdown Table Calculation (Migration Waves)",
#         "question": "Across the three FY2026 migration waves, how many workloads are targeted and what is the total budget? Which wave has the highest budget per workload, and what is it approximately?",
#         "expected_answer": "A total of 50 workloads are targeted (24 + 17 + 9) with a total budget of $11.5M ($1.2M + $3.8M + $6.5M). Wave 3 (October 2026 - March 2027, Tier 1 customer-facing platforms) has the highest budget per workload at about $722,000 ($6.5M / 9). For comparison, Wave 2 is about $223,500 per workload and Wave 1 is $50,000 per workload."
#     },
#     {
#         "id": 7,
#         "category": "PDF Table Calculation (Segment Performance)",
#         "question": "In the Q3 2025 report, which segment had the highest year-on-year revenue growth, what was the growth and its Q3 2025 gross margin? Which segment had the highest gross margin, and what was the company's overall Q3 2025 gross margin?",
#         "expected_answer": "Edge Gateway had the highest YoY revenue growth: 34.5% (from $2,900K in Q3 2024 to $3,900K in Q3 2025), with a Q3 2025 gross margin of 44.0%, the lowest of the three segments. Analytics Suite had the highest gross margin at 71.8% (YoY growth 19.6%). The company's overall Q3 2025 gross margin was 61.8% (gross profit $9,517K on revenue $15,400K), and total revenue grew 20.3% year-on-year."
#     },
#     {
#         "id": 8,
#         "category": "PDF Narrative & KPI Table (Incident & Operations)",
#         "question": "What caused the 14 August 2025 incident in the Q3 2025 report, how long did it last, how many devices were affected and what was done to fix it? Also, was the DSO target met in Q3 2025?",
#         "expected_answer": "On 14 August 2025 the Edge Gateway device-registration service in eu-west-1 had a 23-minute partial degradation. The root cause was an expired internal TLS certificate, because automatic certificate rotation had been disabled during a migration test and not re-enabled. About 1,900 devices could not re-register and no customer data was affected. Remediation: auto-rotation was re-enabled on 15 August 2025 and an alert now fires 30 days before any internal certificate expires. The DSO target was not met: DSO was 47 days against a target of under 45 days (it improved from 53 days in Q3 2024)."
#     },
# ]

def run_rag_evaluation():
    """
    Εκτελεί αυτοματοποιημένα τα test cases περνώντας τα στον Enterprise Agent 
    και συγκρίνει την έξοδο με τα αναμενόμενα αποτελέσματα.
    """
    print("🚀 Εκκίνηση Enterprise RAG Evaluation Pipeline...\n")

    try:
        agent_manager = EnterpriseAgentManager()
        agent_executor = agent_manager.get_agent_executor()
    except Exception as e:
        print(f"❌ Σφάλμα αρχικοποίησης του Agent: {e}")
        return

    results = []

    for test in TEST_CASES:
        print(f"=" * 60)
        print(f"🧪 Test Case #{test['id']} | Κατηγορία: {test['category']}")
        print(f"❓ Ερώτηση: {test['question']}")
        print(f"🎯 Αναμενόμενη Απάντηση (Ground Truth): {test['expected_answer']}")
        print("-" * 60)

        try:
            response = agent_executor.invoke({
                "input": test['question'],
                "chat_history": []
            })

            actual_output = response["output"]
            print(f"🤖 Απάντηση Agent:\n{actual_output}\n")

            results.append({
                "id": test['id'],
                "question": test['question'],
                "expected": test['expected_answer'],
                "actual": actual_output
            })
        except Exception as e:
            print(f"❌ Σφάλμα κατά την εκτέλεση του test case #{test['id']}: {e}\n")

    print("=" * 60)
    print("✅ Η αξιολόγηση ολοκληρώθηκε!")
    print("💡 Μπορείς να ελέγξεις οπτικά αν οι απαντήσεις του Agent ταιριάζουν με το Ground Truth.")


#Ο κλασικός έλεγχος της Python. Διασφαλίζει ότι η συνάρτηση run_rag_evaluation()
#       θα εκτελεστεί αυτόματα μόνο αν τρέξουμε το αρχείο απευθείας από το τερματικό (π.χ. python tests/evaluation.py), και όχι αν το κάνουμε απλώς import σε κάποιο άλλο αρχείο.
if __name__ == "__main__":
    run_rag_evaluation()