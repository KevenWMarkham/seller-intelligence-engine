"""
Seed sample companies, contacts, news items, and tasks for local development.

Creates 3 realistic companies with contacts and seller tasks so the dashboard
has content immediately after setup.

Usage: python scripts/seed_data.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import AsyncSessionLocal, init_db
from src.models.company import Company
from src.models.contact import Contact
from src.models.news import NewsItem
from src.models.task import SellerTask

COMPANIES = [
    {
        "name": "Acme Corp",
        "domain": "acme.com",
        "industry": "Manufacturing",
        "sub_industry": "Discrete Manufacturing",
        "revenue": "$500M-$1B",
        "headcount": 3500,
        "hq_location": "Detroit, MI",
        "stage": "Public",
        "business_model": "B2B",
        "sales_motion": "wedge",
        "description": "Acme Corp is a mid-market industrial manufacturer specializing in precision components for the automotive and aerospace sectors. They are in early stages of digital transformation with limited cloud adoption.",
        "tech_stack_json": json.dumps([
            {"name": "azure", "category": "cloud", "confidence": 0.6, "source": "job_postings"},
            {"name": "terraform", "category": "devops", "confidence": 0.8, "source": "website"},
        ]),
        "platform_adoption_json": json.dumps({
            "microsoft": {"vendor": "microsoft", "depth": "light", "products_detected": ["Azure DevOps"], "evidence": ["azure mentions in job postings"], "confidence_scores": {}},
            "google": {"vendor": "google", "depth": "none", "products_detected": [], "evidence": [], "confidence_scores": {}},
            "aws": {"vendor": "aws", "depth": "none", "products_detected": [], "evidence": [], "confidence_scores": {}},
        }),
    },
    {
        "name": "GlobalData Inc",
        "domain": "globaldata.io",
        "industry": "Financial Services",
        "sub_industry": "Capital Markets",
        "revenue": "$200M-$500M",
        "headcount": 1200,
        "hq_location": "New York, NY",
        "stage": "Private",
        "business_model": "B2B SaaS",
        "sales_motion": "expand",
        "description": "GlobalData provides financial data analytics and risk management solutions to institutional investors. They are an existing Google Cloud customer using BigQuery for data warehousing and are now evaluating Vertex AI.",
        "tech_stack_json": json.dumps([
            {"name": "gcp", "category": "cloud", "confidence": 0.95, "source": "website"},
            {"name": "python", "category": "language", "confidence": 0.9, "source": "job_postings"},
            {"name": "kubernetes", "category": "devops", "confidence": 0.7, "source": "job_postings"},
        ]),
        "platform_adoption_json": json.dumps({
            "google": {"vendor": "google", "depth": "moderate", "products_detected": ["BigQuery", "Google Kubernetes Engine"], "evidence": ["BigQuery mentioned on website", "GCP in job postings"], "confidence_scores": {}},
            "aws": {"vendor": "aws", "depth": "none", "products_detected": [], "evidence": [], "confidence_scores": {}},
            "microsoft": {"vendor": "microsoft", "depth": "none", "products_detected": [], "evidence": [], "confidence_scores": {}},
        }),
    },
    {
        "name": "RetailNow",
        "domain": "retailnow.com",
        "industry": "Retail & CPG",
        "sub_industry": "E-commerce",
        "revenue": "$100M-$200M",
        "headcount": 650,
        "hq_location": "Austin, TX",
        "stage": "Series D",
        "business_model": "Marketplace",
        "sales_motion": "displace",
        "description": "RetailNow operates an omnichannel retail platform for mid-market brands. They are currently deep in AWS but experiencing cost overruns and are evaluating GCP for their data and AI workloads.",
        "tech_stack_json": json.dumps([
            {"name": "aws", "category": "cloud", "confidence": 0.98, "source": "website"},
            {"name": "python", "category": "language", "confidence": 0.9, "source": "job_postings"},
            {"name": "react", "category": "frontend", "confidence": 0.85, "source": "website"},
            {"name": "kubernetes", "category": "devops", "confidence": 0.8, "source": "job_postings"},
        ]),
        "platform_adoption_json": json.dumps({
            "aws": {"vendor": "aws", "depth": "deep", "products_detected": ["EC2", "S3", "RDS", "Lambda"], "evidence": ["AWS mentioned extensively on website", "heavy AWS spend reported in earnings"], "confidence_scores": {}},
            "google": {"vendor": "google", "depth": "evaluating", "products_detected": [], "evidence": ["evaluating GCP for data workloads"], "confidence_scores": {}},
            "microsoft": {"vendor": "microsoft", "depth": "none", "products_detected": [], "evidence": [], "confidence_scores": {}},
        }),
    },
]

CONTACTS = [
    # Acme Corp
    {"company_domain": "acme.com", "name": "Michael Torres", "title": "VP Engineering", "functional_area": "Engineering", "role_type": "decision_maker", "platform_relevance_score": 0.9},
    {"company_domain": "acme.com", "name": "Sandra Lee", "title": "Director of IT", "functional_area": "IT Operations", "role_type": "influencer", "platform_relevance_score": 0.7},
    # GlobalData
    {"company_domain": "globaldata.io", "name": "James Chen", "title": "Chief Data Officer", "functional_area": "Data & Analytics", "role_type": "decision_maker", "platform_relevance_score": 0.95},
    {"company_domain": "globaldata.io", "name": "Priya Nair", "title": "VP Data Engineering", "functional_area": "Engineering", "role_type": "influencer", "platform_relevance_score": 0.85},
    # RetailNow
    {"company_domain": "retailnow.com", "name": "David Kim", "title": "CTO", "functional_area": "Engineering", "role_type": "decision_maker", "platform_relevance_score": 0.95},
    {"company_domain": "retailnow.com", "name": "Rachel Wong", "title": "VP Infrastructure", "functional_area": "IT Operations", "role_type": "influencer", "platform_relevance_score": 0.8},
]

NEWS_ITEMS = [
    {
        "url_hash": "seed-news-001",
        "headline": "Acme Corp announces $50M digital transformation initiative to modernize manufacturing operations",
        "body": "Acme Corp CEO announced a major digital transformation program focused on IoT-enabled manufacturing, predictive maintenance, and supply chain digitization. The company plans to invest $50M over 3 years.",
        "source": "Manufacturing Today",
        "url": "https://example.com/acme-digital-transformation",
        "signal_type": "tech_initiative",
        "urgency": "high",
        "relevance_score": 0.95,
        "opportunity_type": "new_conversation",
        "companies_mentioned_json": json.dumps(["Acme Corp"]),
    },
    {
        "url_hash": "seed-news-002",
        "headline": "GlobalData Inc raises $80M Series D to expand AI-powered risk analytics platform",
        "body": "GlobalData closed an $80M funding round led by Sequoia to accelerate their AI and ML capabilities for institutional risk management. The company plans to hire 200 ML engineers.",
        "source": "TechCrunch",
        "url": "https://example.com/globaldata-funding",
        "signal_type": "earnings",
        "urgency": "high",
        "relevance_score": 0.9,
        "opportunity_type": "upsell",
        "companies_mentioned_json": json.dumps(["GlobalData Inc"]),
    },
    {
        "url_hash": "seed-news-003",
        "headline": "RetailNow reports 40% increase in AWS cloud costs, CFO signals vendor review",
        "body": "RetailNow's Q3 earnings call revealed cloud infrastructure costs surged 40% year-over-year. CFO stated the company is conducting a full vendor review to optimize their cloud spend.",
        "source": "Business Wire",
        "url": "https://example.com/retailnow-cloud-costs",
        "signal_type": "earnings",
        "urgency": "high",
        "relevance_score": 0.98,
        "opportunity_type": "new_conversation",
        "companies_mentioned_json": json.dumps(["RetailNow"]),
    },
]


async def seed():
    await init_db()

    async with AsyncSessionLocal() as session:
        # Companies
        company_map = {}
        for c in COMPANIES:
            company = Company(**{k: v for k, v in c.items() if k != "domain" or True})
            session.add(company)
        await session.flush()

        # Re-query to get IDs
        from sqlalchemy import select
        result = await session.execute(select(Company))
        db_companies = {c.domain: c for c in result.scalars().all()}

        # Contacts
        for c in CONTACTS:
            domain = c.pop("company_domain")
            company = db_companies.get(domain)
            if company:
                contact = Contact(company_id=company.id, **c)
                session.add(contact)

        # News
        for n in NEWS_ITEMS:
            item = NewsItem(**n)
            session.add(item)

        await session.flush()

        # Tasks — one per company
        news_result = await session.execute(select(NewsItem))
        db_news = list(news_result.scalars().all())
        contact_result = await session.execute(select(Contact))
        db_contacts = list(contact_result.scalars().all())

        for i, (domain, company) in enumerate(db_companies.items()):
            news = db_news[i] if i < len(db_news) else None
            contact = next((c for c in db_contacts if c.company_id == company.id and c.role_type == "decision_maker"), None)
            task = SellerTask(
                seller_id="seller-1",
                company_id=company.id,
                contact_id=contact.id if contact else None,
                news_item_id=news.id if news else None,
                platform_vendor="google",
                sales_motion=company.sales_motion,
                priority_score=85 - i * 15,
                status="created",
                coaching_status="not_started",
                conversation_brief_json=json.dumps({
                    "opener": f"I saw that {company.name} recently {news.headline.lower() if news else 'had some interesting developments'}. Wanted to reach out because we're seeing similar companies in your space leverage Google Cloud to address exactly this kind of challenge.",
                    "why_it_matters": f"This directly impacts your role as {contact.title if contact else 'a key leader'} — it represents both a risk and an opportunity.",
                    "solution_connection": f"Google Cloud has specific capabilities that map well to {company.name}'s current priorities.",
                    "suggested_ask": "Would you be open to a 30-minute conversation next week to explore how we've helped similar companies?",
                    "predicted_objections": [
                        {"objection": "We're already committed to our current vendor", "suggested_response": "Completely understand — we're not asking you to replace anything. Let's start by looking at one specific workload where Google can demonstrate clear value alongside what you have."},
                        {"objection": "The timing isn't right", "suggested_response": "Given the recent announcement, the window to shape the strategy is actually right now, before the decisions are locked in. Even a brief conversation could help you frame the requirements better."},
                    ],
                }),
            )
            session.add(task)

        await session.commit()
        print(f"Seeded {len(COMPANIES)} companies, {len(CONTACTS)} contacts, {len(NEWS_ITEMS)} news items, and 3 tasks.")


if __name__ == "__main__":
    asyncio.run(seed())
