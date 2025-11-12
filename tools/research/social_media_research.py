"""Social media research and analytics for legislator accounts."""

from __future__ import annotations

import argparse
import collections
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence

import networkx as nx
import numpy as np
import pandas as pd
from nltk import download as nltk_download
from nltk.sentiment import SentimentIntensityAnalyzer
from psycopg2 import errors, sql
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

from . import common

logger = logging.getLogger(__name__)


@dataclass
class SocialPost:
    member_id: Optional[str]
    platform: str
    post_id: str
    content: str
    posted_at: str
    engagement: Dict[str, Any]
    sentiment: Optional[float]
    hashtags: Sequence[str]
    mentions: Sequence[str]


class SocialMediaResearcher:
    """Compute engagement, sentiment, and topic analytics for social media data."""

    CANDIDATE_TABLES = (
        "analytics.social_media_post",
        "master.social_media_post",
        "master.federal_social_media_post",
    )

    def __init__(
        self,
        days: int = 30,
        limit: int = 2000,
        platforms: Optional[Sequence[str]] = None,
        input_path: Optional[str] = None,
        topics: int = 5,
    ) -> None:
        self.days = days
        self.limit = limit
        self.platforms = [p.lower() for p in platforms] if platforms else None
        self.input_path = input_path
        self.topics = topics

    def fetch_posts(self) -> List[SocialPost]:
        if self.input_path:
            logger.info("Loading posts from %s", self.input_path)
            posts = []
            for entry in common.load_json_lines(self.input_path):
                posts.append(
                    SocialPost(
                        member_id=entry.get("member_id"),
                        platform=entry.get("platform", "unknown"),
                        post_id=str(entry.get("post_id")),
                        content=entry.get("content", ""),
                        posted_at=entry.get("posted_at", ""),
                        engagement=entry.get("engagement_metrics", {}),
                        sentiment=common.safe_float(entry.get("sentiment_score")),
                        hashtags=entry.get("hashtags", []),
                        mentions=entry.get("mentions", []),
                    )
                )
            return posts

        interval = timedelta(days=self.days)
        platforms_filter = sql.SQL("")
        params: List[Any] = [interval, self.limit]
        if self.platforms:
            placeholders = sql.SQL(", ").join(sql.Placeholder() * len(self.platforms))
            platforms_filter = sql.SQL("AND LOWER(platform) IN ({placeholders})").format(placeholders=placeholders)
            params = [interval] + [p.lower() for p in self.platforms] + [self.limit]

        for table in self.CANDIDATE_TABLES:
            query = sql.SQL(
                """
                SELECT
                    member_id,
                    platform,
                    post_id,
                    COALESCE(content, '') AS content,
                    posted_at,
                    COALESCE(engagement_metrics, '{}'::jsonb) AS engagement_metrics,
                    sentiment_score,
                    COALESCE(hashtags, ARRAY[]::text[]) AS hashtags,
                    COALESCE(mentions, ARRAY[]::text[]) AS mentions
                FROM {table}
                WHERE posted_at >= now() - %s
                  {platform_filter}
                ORDER BY posted_at DESC
                LIMIT %s
                """
            ).format(
                table=sql.SQL(table),
                platform_filter=platforms_filter,
            )

            try:
                with common.db_cursor() as cursor:
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                logger.info("Loaded %s posts from %s", len(rows), table)
                return [
                    SocialPost(
                        member_id=row.get("member_id"),
                        platform=row["platform"],
                        post_id=str(row["post_id"]),
                        content=row["content"],
                        posted_at=row["posted_at"].isoformat() if row["posted_at"] else "",
                        engagement=row["engagement_metrics"],
                        sentiment=common.safe_float(row.get("sentiment_score")),
                        hashtags=row["hashtags"],
                        mentions=row["mentions"],
                    )
                    for row in rows
                ]
            except errors.UndefinedTable:
                logger.debug("Table %s missing; trying next candidate", table)
                continue

        logger.warning("No social media tables found; returning empty dataset")
        return []

    def compute_engagement(self, posts: Sequence[SocialPost]) -> Dict[str, Any]:
        per_platform: Dict[str, Dict[str, float]] = collections.defaultdict(lambda: collections.defaultdict(float))
        totals = collections.defaultdict(float)
        for post in posts:
            metrics = post.engagement or {}
            for key, value in metrics.items():
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    continue
                per_platform[post.platform][key] += value
                totals[key] += value
        return {
            "per_platform": {platform: dict(values) for platform, values in per_platform.items()},
            "totals": dict(totals),
        }

    def compute_sentiment(self, posts: Sequence[SocialPost]) -> Dict[str, Any]:
        if not posts:
            return {"records": 0, "mean_compound": None, "distribution": {}}

        nltk_download("vader_lexicon", quiet=True)
        analyzer = SentimentIntensityAnalyzer()
        distribution: Dict[str, int] = collections.Counter()
        compounds: List[float] = []

        for post in posts:
            if post.sentiment is not None:
                compound = post.sentiment
            else:
                compound = analyzer.polarity_scores(post.content)["compound"]
            compounds.append(compound)
            bucket = "neutral"
            if compound >= 0.05:
                bucket = "positive"
            elif compound <= -0.05:
                bucket = "negative"
            distribution[bucket] += 1

        return {
            "records": len(posts),
            "mean_compound": float(np.mean(compounds)) if compounds else None,
            "distribution": dict(distribution),
        }

    def compute_topics(self, posts: Sequence[SocialPost]) -> List[Dict[str, Any]]:
        if not posts or self.topics <= 0:
            return []
        texts = [post.content for post in posts if post.content]
        if not texts:
            return []

        vectorizer = CountVectorizer(stop_words="english", max_features=5000)
        document_term = vectorizer.fit_transform(texts)
        n_components = min(self.topics, document_term.shape[0])
        if n_components == 0:
            return []

        lda = LatentDirichletAllocation(n_components=n_components, random_state=42, learning_method="online")
        lda.fit(document_term)

        feature_names = vectorizer.get_feature_names_out()
        topics: List[Dict[str, Any]] = []
        for idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[::-1][:10]
            topics.append({"topic": idx, "top_terms": [feature_names[i] for i in top_indices]})
        return topics

    def aggregate_hashtags(self, posts: Sequence[SocialPost]) -> List[Dict[str, Any]]:
        counter: Dict[str, int] = collections.Counter()
        for post in posts:
            counter.update([tag.lower() for tag in post.hashtags])
        return [
            {"hashtag": tag, "count": count}
            for tag, count in counter.most_common(25)
        ]

    def build_mention_network(self, posts: Sequence[SocialPost]) -> Dict[str, Any]:
        graph = nx.DiGraph()
        for post in posts:
            source = post.member_id or f"{post.platform}:{post.post_id}"
            for mention in post.mentions:
                target = mention.lower()
                if graph.has_edge(source, target):
                    graph[source][target]["weight"] += 1
                else:
                    graph.add_edge(source, target, weight=1)
        centrality = nx.degree_centrality(graph) if graph.number_of_nodes() else {}
        top_nodes = sorted(centrality.items(), key=lambda item: item[1], reverse=True)[:15]
        edges = [
            {"source": u, "target": v, "weight": data["weight"]}
            for u, v, data in graph.edges(data=True)
        ]
        return {
            "nodes": [{"id": node, "centrality": score} for node, score in top_nodes],
            "edges": edges,
        }

    def run(self) -> Dict[str, Any]:
        posts = self.fetch_posts()
        engagement = self.compute_engagement(posts)
        sentiment = self.compute_sentiment(posts)
        topics = self.compute_topics(posts)
        hashtags = self.aggregate_hashtags(posts)
        mention_network = self.build_mention_network(posts)

        dataframe = pd.DataFrame(
            [
                {
                    "member_id": post.member_id,
                    "platform": post.platform,
                    "post_id": post.post_id,
                    "posted_at": post.posted_at,
                    "engagement": post.engagement,
                    "sentiment": post.sentiment,
                }
                for post in posts
            ]
        )

        summary = {
            "metadata": {
                "days": self.days,
                "limit": self.limit,
                "platforms": self.platforms,
                "topics": self.topics,
                "records": len(posts),
            },
            "engagement": engagement,
            "sentiment": sentiment,
            "topics": topics,
            "hashtags": hashtags,
            "mention_network": mention_network,
            "records": dataframe.to_dict(orient="records"),
        }
        return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Social media research analytics")
    parser.add_argument("--days", type=int, default=30, help="Number of days of posts to analyze")
    parser.add_argument("--limit", type=int, default=2000, help="Maximum posts to load")
    parser.add_argument("--platform", action="append", help="Limit analysis to a platform (repeatable)")
    parser.add_argument("--input", help="Optional JSON lines file as offline data source")
    parser.add_argument("--topics", type=int, default=5, help="Number of topics to compute")
    parser.add_argument("--output", help="Directory to write JSON report into")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    common.configure_logging(args.verbose)
    researcher = SocialMediaResearcher(
        days=args.days,
        limit=args.limit,
        platforms=args.platform,
        input_path=args.input,
        topics=args.topics,
    )
    summary = researcher.run()

    if args.output:
        output_dir = common.ensure_report_dir(path=args.output)
        path = output_dir / "social_media_research.json"
    else:
        path = common.timestamped_filename("social_media_research")

    common.dump_json(summary, path)
    logger.info("Wrote social media research report to %s", path)


if __name__ == "__main__":  # pragma: no cover
    main()
