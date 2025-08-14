"""
Document generation tools for business reports and analysis.
"""
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path


class DocumentGenerator:
    """Generate structured business documents and reports."""

    def __init__(self, output_dir: str = "data/generated_docs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_business_plan(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive business plan."""
        template = """
# Business Plan: {business_name}

## Executive Summary
{executive_summary}

## Business Description
**Industry:** {industry}
**Target Market:** {target_market}
**Business Model:** {business_model}
**Region:** {region}

## Market Analysis
{market_analysis}

## Financial Projections
{financial_projections}

## Risk Assessment
{risk_assessment}

## Implementation Timeline
{implementation_timeline}

## Funding Requirements
{funding_requirements}

---
*Generated on {generation_date}*
"""

        content = template.format(
            business_name=business_data.get('name', 'New Business Venture'),
            executive_summary=business_data.get('executive_summary', 'Business executive summary'),
            industry=business_data.get('industry', 'Not specified'),
            target_market=business_data.get('target_market', 'Not specified'),
            business_model=business_data.get('business_model', 'Not specified'),
            region=business_data.get('region', 'Not specified'),
            market_analysis=business_data.get('market_analysis', 'Market analysis pending'),
            financial_projections=business_data.get('financial_projections', 'Financial projections pending'),
            risk_assessment=business_data.get('risk_assessment', 'Risk assessment pending'),
            implementation_timeline=business_data.get('implementation_timeline', 'Timeline pending'),
            funding_requirements=business_data.get('funding_requirements', 'Funding requirements pending'),
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Save to file
        filename = f"business_plan_{
            business_data.get(
                'name',
                'unnamed').replace(
                ' ',
                '_')}_{
            datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = self.output_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            'document_type': 'business_plan',
            'filename': filename,
            'file_path': str(file_path),
            'content': content,
            'word_count': len(content.split())
        }

    def generate_market_analysis_report(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate market analysis report."""
        template = """
# Market Analysis Report: {industry}

## Market Overview
**Market Size:** {market_size}
**Growth Rate:** {growth_rate}
**Analysis Date:** {analysis_date}

## Key Market Trends
{market_trends}

## Competitive Landscape
{competitive_landscape}

## Market Opportunities
{opportunities}

## Market Challenges
{challenges}

## Recommendations
{recommendations}

---
*Report generated on {generation_date}*
"""

        # Format market trends
        trends_text = ""
        if market_data.get('trends'):
            for i, trend in enumerate(market_data['trends'], 1):
                trends_text += f"{i}. **{trend.get('name',
                                                   'Trend')}**: {trend.get('description',
                                                                           'Description')}\n"

        # Format competitive landscape
        competitors_text = ""
        if market_data.get('competitors'):
            for competitor in market_data['competitors']:
                competitors_text += f"- **{competitor.get('name',
                                                          'Competitor')}**: {competitor.get('description',
                                                                                            'Description')}\n"

        content = template.format(
            industry=market_data.get('industry', 'Industry Analysis'),
            market_size=market_data.get('market_size', 'Size not specified'),
            growth_rate=market_data.get('growth_rate', 'Growth rate not specified'),
            analysis_date=market_data.get('analysis_date', datetime.now().strftime("%Y-%m-%d")),
            market_trends=trends_text or "No specific trends identified",
            competitive_landscape=competitors_text or "Competitive analysis pending",
            opportunities=market_data.get('opportunities', 'Market opportunities to be identified'),
            challenges=market_data.get('challenges', 'Market challenges to be identified'),
            recommendations=market_data.get('recommendations', 'Recommendations to be developed'),
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Save to file
        filename = f"market_analysis_{
            market_data.get(
                'industry',
                'industry').replace(
                ' ',
                '_')}_{
            datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = self.output_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            'document_type': 'market_analysis',
            'filename': filename,
            'file_path': str(file_path),
            'content': content,
            'word_count': len(content.split())
        }

    def generate_financial_model(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial model document."""
        template = """
# Financial Model: {business_name}

## Key Assumptions
{assumptions}

## Revenue Projections (5-Year)
{revenue_projections}

## Cost Structure
{cost_structure}

## Profitability Analysis
{profitability_analysis}

## Cash Flow Projections
{cash_flow}

## Key Financial Metrics
{financial_metrics}

## Sensitivity Analysis
{sensitivity_analysis}

## Funding Requirements
{funding_requirements}

---
*Financial model generated on {generation_date}*
"""

        # Format revenue projections
        revenue_text = ""
        if financial_data.get('revenue_projections'):
            projections = financial_data['revenue_projections']
            for year, revenue in projections.items():
                revenue_text += f"- **Year {year}:** ${revenue:,.0f}\n"

        # Format financial metrics
        metrics_text = ""
        if financial_data.get('metrics'):
            for metric, value in financial_data['metrics'].items():
                if isinstance(value, (int, float)):
                    if 'rate' in metric.lower() or 'margin' in metric.lower():
                        metrics_text += f"- **{metric.title()}:** {value:.1f}%\n"
                    else:
                        metrics_text += f"- **{metric.title()}:** ${value:,.0f}\n"
                else:
                    metrics_text += f"- **{metric.title()}:** {value}\n"

        content = template.format(
            business_name=financial_data.get(
                'business_name',
                'Business Financial Model'),
            assumptions=financial_data.get(
                'assumptions',
                'Key assumptions to be documented'),
            revenue_projections=revenue_text or "Revenue projections to be developed",
            cost_structure=financial_data.get(
                'cost_structure',
                'Cost structure to be analyzed'),
            profitability_analysis=financial_data.get(
                'profitability_analysis',
                'Profitability analysis pending'),
            cash_flow=financial_data.get(
                'cash_flow',
                'Cash flow analysis pending'),
            financial_metrics=metrics_text or "Financial metrics to be calculated",
            sensitivity_analysis=financial_data.get(
                'sensitivity_analysis',
                'Sensitivity analysis to be performed'),
            funding_requirements=financial_data.get(
                'funding_requirements',
                'Funding requirements to be determined'),
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Save to file
        filename = f"financial_model_{
            financial_data.get(
                'business_name',
                'business').replace(
                ' ',
                '_')}_{
            datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = self.output_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            'document_type': 'financial_model',
            'filename': filename,
            'file_path': str(file_path),
            'content': content,
            'word_count': len(content.split())
        }

    def generate_risk_assessment(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk assessment document."""
        template = """
# Risk Assessment: {business_name}

## Executive Summary
{executive_summary}

## Identified Risks

### Market Risks
{market_risks}

### Financial Risks
{financial_risks}

### Operational Risks
{operational_risks}

### Legal & Regulatory Risks
{legal_risks}

### Technology Risks
{technology_risks}

## Risk Mitigation Strategies
{mitigation_strategies}

## Risk Monitoring Plan
{monitoring_plan}

---
*Risk assessment completed on {generation_date}*
"""

        # Format risks by category
        def format_risks(risks_list):
            if not risks_list:
                return "No specific risks identified in this category"

            formatted = ""
            for risk in risks_list:
                if isinstance(risk, dict):
                    formatted += f"- **{risk.get('name',
                                                 'Risk')}** (Impact: {risk.get('impact',
                                                                               'Unknown')}, Probability: {risk.get('probability',
                                                                                                                   'Unknown')})\n"
                    formatted += f"  {risk.get('description', 'No description provided')}\n"
                else:
                    formatted += f"- {risk}\n"
            return formatted

        content = template.format(
            business_name=risk_data.get('business_name', 'Business Risk Assessment'),
            executive_summary=risk_data.get('executive_summary', 'Risk assessment summary'),
            market_risks=format_risks(risk_data.get('market_risks', [])),
            financial_risks=format_risks(risk_data.get('financial_risks', [])),
            operational_risks=format_risks(risk_data.get('operational_risks', [])),
            legal_risks=format_risks(risk_data.get('legal_risks', [])),
            technology_risks=format_risks(risk_data.get('technology_risks', [])),
            mitigation_strategies=risk_data.get('mitigation_strategies', 'Risk mitigation strategies to be developed'),
            monitoring_plan=risk_data.get('monitoring_plan', 'Risk monitoring plan to be established'),
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Save to file
        filename = f"risk_assessment_{
            risk_data.get(
                'business_name',
                'business').replace(
                ' ',
                '_')}_{
            datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = self.output_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            'document_type': 'risk_assessment',
            'filename': filename,
            'file_path': str(file_path),
            'content': content,
            'word_count': len(content.split())
        }

    def generate_executive_summary(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary from session data."""
        template = """
# Executive Summary: {business_name}

## Business Overview
{business_overview}

## Market Opportunity
{market_opportunity}

## Competitive Advantage
{competitive_advantage}

## Financial Highlights
{financial_highlights}

## Key Risks & Mitigation
{key_risks}

## Funding Requirements
{funding_requirements}

## Next Steps
{next_steps}

---
*Executive summary generated on {generation_date} from business intelligence analysis*
"""

        content = template.format(
            business_name=session_data.get('business_name', 'Business Venture'),
            business_overview=session_data.get('business_overview', 'Business overview from analysis'),
            market_opportunity=session_data.get('market_opportunity', 'Market opportunity identified'),
            competitive_advantage=session_data.get('competitive_advantage', 'Competitive advantages noted'),
            financial_highlights=session_data.get('financial_highlights', 'Financial projections summarized'),
            key_risks=session_data.get('key_risks', 'Primary risks and mitigation strategies'),
            funding_requirements=session_data.get('funding_requirements', 'Funding needs assessment'),
            next_steps=session_data.get('next_steps', 'Recommended next steps'),
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Save to file
        filename = f"executive_summary_{
            session_data.get(
                'business_name',
                'business').replace(
                ' ',
                '_')}_{
            datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        file_path = self.output_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            'document_type': 'executive_summary',
            'filename': filename,
            'file_path': str(file_path),
            'content': content,
            'word_count': len(content.split())
        }

    def list_generated_documents(self) -> List[Dict[str, Any]]:
        """List all generated documents."""
        documents = []

        for file_path in self.output_dir.glob("*.md"):
            stat = file_path.stat()
            documents.append({
                'filename': file_path.name,
                'file_path': str(file_path),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })

        # Sort by creation time, newest first
        documents.sort(key=lambda x: x['created'], reverse=True)
        return documents


def create_document_tool_spec():
    """Create tool specification for AG2 integration."""
    return {
        "name": "document_generator",
        "description": "Generate business documents including business plans, market analysis, financial models, and risk assessments",
        "parameters": {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "enum": [
                        "business_plan",
                        "market_analysis",
                        "financial_model",
                        "risk_assessment",
                        "executive_summary"],
                    "description": "Type of document to generate"},
                "data": {
                    "type": "object",
                    "description": "Data to include in the document"}},
            "required": [
                "document_type",
                "data"]}}


def document_tool_executor(document_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute document generation for AG2."""
    generator = DocumentGenerator()

    if document_type == "business_plan":
        return generator.generate_business_plan(data)

    elif document_type == "market_analysis":
        return generator.generate_market_analysis_report(data)

    elif document_type == "financial_model":
        return generator.generate_financial_model(data)

    elif document_type == "risk_assessment":
        return generator.generate_risk_assessment(data)

    elif document_type == "executive_summary":
        return generator.generate_executive_summary(data)

    else:
        return {"error": f"Unknown document type: {document_type}"}
