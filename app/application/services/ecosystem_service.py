from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.exceptions import NotFoundError
from app.domain.models.api_client import APIClient
from app.domain.models.marketplace_listing import MarketplaceListing
from app.domain.models.marketplace_review import MarketplaceReview
from app.domain.models.plugin_registry import PluginRegistry
from app.domain.models.resource import Resource
from app.domain.models.subscription_plan import SubscriptionPlan
from app.domain.models.tenant_subscription import TenantSubscription


class EcosystemService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_marketplace(self, *, tenant_id: int) -> list[MarketplaceListing]:
        result = await self.session.execute(
            select(MarketplaceListing)
            .where(MarketplaceListing.tenant_id == tenant_id, MarketplaceListing.is_published.is_(True))
            .order_by(MarketplaceListing.average_rating.desc(), MarketplaceListing.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_listing(
        self,
        *,
        tenant_id: int,
        teacher_user_id: int,
        topic_id: int | None,
        resource_id: int | None,
        listing_type: str,
        title: str,
        summary: str,
        price_cents: int,
        currency: str,
    ) -> MarketplaceListing:
        if resource_id is not None:
            resource = await self.session.get(Resource, resource_id)
            if resource is None or int(resource.tenant_id) != tenant_id:
                raise NotFoundError("Resource not found")

        row = MarketplaceListing(
            tenant_id=tenant_id,
            teacher_user_id=teacher_user_id,
            topic_id=topic_id,
            resource_id=resource_id,
            listing_type=listing_type.strip(),
            title=title.strip(),
            summary=summary.strip(),
            price_cents=price_cents,
            currency=currency.strip().upper(),
            is_published=True,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def create_review(
        self,
        *,
        tenant_id: int,
        listing_id: int,
        reviewer_user_id: int,
        rating: int,
        headline: str,
        review_text: str,
    ) -> MarketplaceReview:
        listing = await self.session.get(MarketplaceListing, listing_id)
        if listing is None or int(listing.tenant_id) != tenant_id:
            raise NotFoundError("Marketplace listing not found")

        review = MarketplaceReview(
            tenant_id=tenant_id,
            listing_id=listing_id,
            reviewer_user_id=reviewer_user_id,
            rating=rating,
            headline=headline.strip(),
            review_text=review_text.strip(),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(review)
        await self.session.flush()

        agg = await self.session.execute(
            select(func.avg(MarketplaceReview.rating), func.count(MarketplaceReview.id))
            .where(MarketplaceReview.tenant_id == tenant_id, MarketplaceReview.listing_id == listing_id)
        )
        avg_rating, review_count = agg.one()
        listing.average_rating = round(float(avg_rating or 0.0), 2)
        listing.review_count = int(review_count or 0)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def list_plugins(self, *, tenant_id: int) -> list[PluginRegistry]:
        result = await self.session.execute(
            select(PluginRegistry).where(PluginRegistry.tenant_id == tenant_id).order_by(PluginRegistry.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_plugin(
        self,
        *,
        tenant_id: int,
        key: str,
        name: str,
        plugin_type: str,
        provider: str,
        version: str,
        config_json: str,
    ) -> PluginRegistry:
        row = PluginRegistry(
            tenant_id=tenant_id,
            key=key.strip(),
            name=name.strip(),
            plugin_type=plugin_type.strip(),
            provider=provider.strip(),
            version=version.strip(),
            config_json=config_json,
            is_enabled=True,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def list_api_clients(self, *, tenant_id: int) -> list[APIClient]:
        result = await self.session.execute(select(APIClient).where(APIClient.tenant_id == tenant_id).order_by(APIClient.created_at.desc()))
        return list(result.scalars().all())

    async def create_api_client(self, *, tenant_id: int, name: str, scopes: list[str], rate_limit_per_minute: int) -> APIClient:
        row = APIClient(
            tenant_id=tenant_id,
            name=name.strip(),
            client_key=f"lp_{secrets.token_hex(16)}",
            scopes_json=json.dumps(scopes, ensure_ascii=True),
            rate_limit_per_minute=rate_limit_per_minute,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def list_subscription_plans(self) -> list[SubscriptionPlan]:
        result = await self.session.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.is_active.is_(True)).order_by(SubscriptionPlan.monthly_price_cents.asc())
        )
        return list(result.scalars().all())

    async def create_subscription_plan(
        self,
        *,
        tenant_id: int | None,
        code: str,
        name: str,
        monthly_price_cents: int,
        usage_price_cents: int,
        features: list[str],
    ) -> SubscriptionPlan:
        row = SubscriptionPlan(
            tenant_id=tenant_id,
            code=code.strip(),
            name=name.strip(),
            monthly_price_cents=monthly_price_cents,
            usage_price_cents=usage_price_cents,
            features_json=json.dumps(features, ensure_ascii=True),
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def assign_subscription(self, *, tenant_id: int, plan_id: int, seats: int) -> TenantSubscription:
        plan = await self.session.get(SubscriptionPlan, plan_id)
        if plan is None:
            raise NotFoundError("Subscription plan not found")

        row = TenantSubscription(
            tenant_id=tenant_id,
            plan_id=plan_id,
            status="active",
            seats=seats,
            monthly_usage_units=max(1000, seats * 120),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            created_at=datetime.now(timezone.utc),
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get_overview(self, *, tenant_id: int) -> dict:
        listing_count = await self.session.scalar(select(func.count(MarketplaceListing.id)).where(MarketplaceListing.tenant_id == tenant_id))
        course_count = await self.session.scalar(
            select(func.count(MarketplaceListing.id)).where(MarketplaceListing.tenant_id == tenant_id, MarketplaceListing.listing_type == "course")
        )
        plugin_count = await self.session.scalar(select(func.count(PluginRegistry.id)).where(PluginRegistry.tenant_id == tenant_id))
        api_client_count = await self.session.scalar(select(func.count(APIClient.id)).where(APIClient.tenant_id == tenant_id))
        active_subscription_result = await self.session.execute(
            select(TenantSubscription).where(TenantSubscription.tenant_id == tenant_id).order_by(TenantSubscription.created_at.desc()).limit(1)
        )
        active_subscription = active_subscription_result.scalar_one_or_none()

        monetization_snapshot = {
            "marketplace_gmv_cents": int(
                await self.session.scalar(
                    select(func.coalesce(func.sum(MarketplaceListing.price_cents), 0)).where(
                        MarketplaceListing.tenant_id == tenant_id,
                        MarketplaceListing.is_published.is_(True),
                    )
                )
                or 0
            ),
            "subscription_mrr_cents": 0,
            "active_plan": None,
        }
        if active_subscription is not None:
            plan = await self.session.get(SubscriptionPlan, active_subscription.plan_id)
            monetization_snapshot["subscription_mrr_cents"] = int(plan.monthly_price_cents if plan is not None else 0)
            monetization_snapshot["active_plan"] = plan.name if plan is not None else None

        return {
            "marketplace_listing_count": int(listing_count or 0),
            "published_course_count": int(course_count or 0),
            "plugin_count": int(plugin_count or 0),
            "api_client_count": int(api_client_count or 0),
            "active_subscription": active_subscription,
            "monetization_snapshot": monetization_snapshot,
        }
