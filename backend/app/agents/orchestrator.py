from __future__ import annotations
from typing import Dict, Any
from app.agents.data_auditor import DataAuditor
from app.agents.bias_hunter import BiasHunter
from app.agents.explainability_agent import ExplainabilityAgent
from app.agents.remediation_agent import RemediationAgent


class Orchestrator:
    def __init__(self, df, target_column: str):
        self.df = df
        self.target = target_column
        self.data_auditor = DataAuditor(df)
        self.bias_hunter = BiasHunter(df, target_column)
        self.explain_agent = ExplainabilityAgent(df, target_column)
        self.remediation = RemediationAgent(df, target_column)

    def run(self) -> Dict[str, Any]:
        report = {}
        report["data_quality"] = self.data_auditor.run()
        report["bias_findings"] = self.bias_hunter.run()
        report["explainability"] = self.explain_agent.run()
        report["remediation"] = self.remediation.run()
        return report
