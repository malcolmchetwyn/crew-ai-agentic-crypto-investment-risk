import yaml
from crewai import Task
from typing import Any, Optional, Dict


class CryptoAnalysisTasks:
    """
    Factory for creating Task objects for crypto analysis workflows.
    Loads task templates and framework definitions from YAML configs.
    """

    def __init__(
        self,
        tasks_path: str = './src/config/tasks.yaml',
        scoring_path: str = './src/config/scoring.yaml'
    ) -> None:
        try:
            with open(tasks_path, 'r') as f:
                self.config: Dict[str, Any] = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Tasks configuration file not found: {tasks_path}")

        try:
            with open(scoring_path, 'r') as f:
                self.framework: Dict[str, Any] = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Scoring configuration file not found: {scoring_path}")

    def _create_task(
        self,
        name: str,
        agent: Any,
        context: Optional[Any] = None,
        **kwargs
    ) -> Task:
        task_config = self.config.get(name)
        if not task_config:
            raise KeyError(f"Task config '{name}' not found in tasks configuration.")

        description = task_config.get('description', '').format(**kwargs)
        expected_output = task_config.get('expected_output', '').format(**kwargs)

        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            context=context,
            human_input=False
        )

    def screener_task(self, agent: Any, crypto_symbol: str) -> Task:
        filters = self.framework.get('hard_filters', {})
        if not filters:
            raise KeyError("No 'hard_filters' found in scoring configuration.")

        lines = []
        for key, cfg in filters.items():
            desc = cfg.get('description', key)
            if 'options' in cfg:
                opts = ' OR '.join(
                    f"{opt['metric']} {opt['operator']} {opt['value']}"
                    for opt in cfg['options']
                )
                lines.append(f"- **{desc}**: {opts}")
            elif 'conditions' in cfg:
                conds = ' AND '.join(
                    f"{c['metric']} {c['operator']} {c['value']}"
                    for c in cfg['conditions']
                )
                lines.append(f"- **{desc}**: {conds}")
            else:
                lines.append(f"- **{desc}**: must be {cfg['operator']} {cfg['value']}")

        description = f"""
For the cryptocurrency '{crypto_symbol}', you MUST:
1. **Data Gathering & Verification**: cross‑check each metric across at least three reputable sources and report the average value.
2. **Hard Filtering**: verify ALL of the following:
{chr(10).join(lines)}
""".strip()

        output_templ = self.config.get('screener_task', {}).get('expected_output', '')
        expected_output = output_templ.format(crypto_symbol=crypto_symbol)

        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            context=None,
            human_input=False
        )

    def quant_task(self, agent: Any, crypto_symbol: str, context: Any) -> Task:
        description = f"""
You have received a data report for **{crypto_symbol}** that has passed all hard filters.
Your task is to perform a deep quantitative analysis and score it from **0–100** using the following buckets and weights:

- **Native‑Demand Mechanics (25%)**  
  Calculate `onchain_sink_pct` = (annual on‑chain spend or stake) / circulating_supply.  
  **Sub‑score** (0–10) = log10(onchain_sink_pct * 100) * 4 (Clamp to [0,10].)

- **Valuation Realism (18%)**  
  Based on FDV / Revenue:  
  - ≤ 10× → 10 pts  
  - > 10× and ≤ 15× → 6 pts  
  - > 15× → 0 pts

- **Dev Traction (18%)**  
  Given `commit_percentile_90d` (0–100):  
  **Sub‑score** (0–10) = min((commit_percentile_90d ** 2) / 10, 10)

- **Unlock / Inflation (10%)**  
  Let u = `unlock_12mo_pct`.  
  - u ≤ 0.15 → 10 pts  
  - 0.15 < u < 0.40 → linearly interpolate 10→0  
  - u ≥ 0.40 → 0 pts

- **Catalyst Clock (10%)**  
  - ≥ 2 scheduled high‑impact releases next 12 mo → 10 pts  
  - 1 release → 5 pts  
  - 0 → 0 pts

- **Regulatory & Moat Combo (10%)**  
  Combine `regulatory_risk_score` (0–5) and `moat_score` (0–10):  
  sub_score = clamp(10 - (regulatory_risk_score * 1.5) + (moat_score * 0.5), 0, 10)

- **Liquidity & Custody (5%)**  
  - Trades on ≥ 3 top‑10 exchanges **and** full hardware‑wallet support → 10 pts  
  - Otherwise → 0 pts

For each bucket, show:
1. Raw metric(s).
2. Formula.
3. Sub‑score.

Then compute **Total Quantitative Score** out of 100:
Total = (NativeDemand * 0.25)
    + (Valuation * 0.18)
    + (DevTraction * 0.18)
    + (UnlockInflation * 0.10)
    + (CatalystClock * 0.10)
    + (RegMoat * 0.10)
    + (LiquidityCustody * 0.05)
""".strip()

        output_templ = self.config.get('quant_task', {}).get('expected_output', '')
        expected_output = output_templ.format(crypto_symbol=crypto_symbol)

        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            context=context,
            human_input=False
        )

    def analyst_task(self, agent: Any, crypto_symbol: str, context: Any) -> Task:
        return self._create_task(
            'analyst_task',
            agent,
            context=context,
            crypto_symbol=crypto_symbol
        )

    def synthesizer_task(self, agent: Any, crypto_symbol: str, context: Any) -> Task:
        return self._create_task(
            'synthesizer_task',
            agent,
            context=context,
            crypto_symbol=crypto_symbol
        )


    def fact_checker_task(self, agent: Any, context: Any) -> Task:
        """Creates the quantitative data verification task."""
        return self._create_task(
            'fact_checker_task',
            agent,
            context=context
        )

    def qualitative_verification_task(self, agent: Any, context: Any) -> Task:
        """Creates the qualitative claim verification task."""
        return self._create_task(
            'qualitative_verification_task',
            agent,
            context=context
        )