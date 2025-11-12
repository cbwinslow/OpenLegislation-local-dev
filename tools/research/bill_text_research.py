"""Bill text research utilities for OpenLegislation data."""

from __future__ import annotations

import argparse
import collections
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd
from nltk import download as nltk_download
from nltk.sentiment import SentimentIntensityAnalyzer
from psycopg2 import sql
from psycopg2 import errors
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from . import common

logger = logging.getLogger(__name__)


@dataclass
class BillRecord:
    bill_print_no: str
    bill_session_year: int
    version_id: str
    content: str
    subjects: Sequence[str]

    @property
    def word_count(self) -> int:
        return len(self.content.split())


class BillTextResearcher:
    """Conduct NLP-driven research on federal bill texts."""

    def __init__(
        self,
        limit: int = 200,
        min_words: int = 100,
        session_year: int | None = None,
        topics: int = 5,
    ) -> None:
        self.limit = limit
        self.min_words = min_words
        self.session_year = session_year
        self.topics = topics

    def fetch_bills(self) -> List[BillRecord]:
        logger.info("Fetching up to %s bill texts", self.limit)
        query = sql.SQL(
            """
            SELECT
                t.bill_print_no,
                t.bill_session_year,
                t.version_id,
                t.content,
                COALESCE(array_remove(array_agg(DISTINCT s.subject), NULL), ARRAY[]::text[]) AS subjects
            FROM master.federal_bill_text AS t
            LEFT JOIN master.federal_bill_subject AS s
                ON s.bill_print_no = t.bill_print_no
               AND s.bill_session_year = t.bill_session_year
            WHERE t.text_format = 'plain'
              AND t.content IS NOT NULL
              {session_filter}
            GROUP BY t.bill_print_no, t.bill_session_year, t.version_id, t.content
            ORDER BY t.created_date_time DESC
            LIMIT %s
            """
        ).format(
            session_filter=sql.SQL("AND t.bill_session_year = %s") if self.session_year else sql.SQL("")
        )

        params: List[Any] = []
        if self.session_year:
            params.append(self.session_year)
        params.append(self.limit)

        try:
            with common.db_cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        except errors.UndefinedTable:
            logger.warning(
                "federal bill tables missing; returning empty dataset. Have you run the federal ingestion migrations?"
            )
            rows = []

        records = [
            BillRecord(
                bill_print_no=row["bill_print_no"],
                bill_session_year=int(row["bill_session_year"]),
                version_id=row["version_id"],
                content=row["content"],
                subjects=row["subjects"],
            )
            for row in rows
        ]

        filtered = [record for record in records if record.word_count >= self.min_words]
        logger.info("Loaded %s records after filtering by minimum words", len(filtered))
        return filtered

    def compute_sentiment(self, records: Sequence[BillRecord]) -> Dict[str, Any]:
        if not records:
            return {"records": 0, "mean_compound": None, "distribution": {}}

        nltk_download("vader_lexicon", quiet=True)
        analyzer = SentimentIntensityAnalyzer()
        distribution: Dict[str, int] = collections.Counter()
        compounds: List[float] = []

        for record in records:
            sentiment = analyzer.polarity_scores(record.content)
            compound = sentiment["compound"]
            compounds.append(compound)
            bucket = "neutral"
            if compound >= 0.05:
                bucket = "positive"
            elif compound <= -0.05:
                bucket = "negative"
            distribution[bucket] += 1

        mean_compound = float(np.mean(compounds)) if compounds else None
        stdev = float(np.std(compounds)) if len(compounds) > 1 else 0.0

        return {
            "records": len(records),
            "mean_compound": mean_compound,
            "stdev_compound": stdev,
            "distribution": distribution,
        }

    def compute_top_terms(self, records: Sequence[BillRecord], top_k: int = 20) -> List[Dict[str, Any]]:
        if not records:
            return []

        texts = [record.content for record in records]
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(texts)
        scores = tfidf_matrix.mean(axis=0)
        scores = np.asarray(scores).ravel()
        terms = vectorizer.get_feature_names_out()

        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            {"term": terms[idx], "score": float(scores[idx])}
            for idx in top_indices
        ]

    def compute_topics(self, records: Sequence[BillRecord]) -> List[Dict[str, Any]]:
        if not records or self.topics <= 0:
            return []

        texts = [record.content for record in records]
        vectorizer = CountVectorizer(stop_words="english", max_features=5000)
        document_term = vectorizer.fit_transform(texts)

        n_components = min(self.topics, document_term.shape[0])
        if n_components == 0:
            return []

        lda = LatentDirichletAllocation(
            n_components=n_components,
            random_state=42,
            learning_method="online",
        )
        lda.fit(document_term)

        feature_names = vectorizer.get_feature_names_out()
        topics: List[Dict[str, Any]] = []
        for topic_idx, topic in enumerate(lda.components_):
            top_indices = topic.argsort()[::-1][:10]
            topics.append(
                {
                    "topic": topic_idx,
                    "top_terms": [feature_names[i] for i in top_indices],
                }
            )
        return topics

    def summarize_subjects(self, records: Sequence[BillRecord]) -> List[Dict[str, Any]]:
        counter: Dict[str, int] = collections.Counter()
        for record in records:
            counter.update(record.subjects)
        return [
            {"subject": subject, "count": count}
            for subject, count in counter.most_common(25)
        ]

    def to_dataframe(self, records: Sequence[BillRecord]) -> pd.DataFrame:
        rows = [
            {
                "bill_print_no": record.bill_print_no,
                "session_year": record.bill_session_year,
                "version_id": record.version_id,
                "subjects": list(record.subjects),
                "word_count": record.word_count,
            }
            for record in records
        ]
        return pd.DataFrame(rows)

    def run(self) -> Dict[str, Any]:
        records = self.fetch_bills()
        sentiment = self.compute_sentiment(records)
        top_terms = self.compute_top_terms(records)
        topics = self.compute_topics(records)
        subjects = self.summarize_subjects(records)
        dataframe = self.to_dataframe(records)

        summary = {
            "metadata": {
                "limit": self.limit,
                "min_words": self.min_words,
                "session_year": self.session_year,
                "topics": self.topics,
                "records": len(records),
                "mean_word_count": float(dataframe["word_count"].mean()) if not dataframe.empty else None,
            },
            "sentiment": sentiment,
            "top_terms": top_terms,
            "topics": topics,
            "subjects": subjects,
            "records": dataframe.to_dict(orient="records"),
        }
        return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research analysis for federal bill text")
    parser.add_argument("--limit", type=int, default=200, help="Maximum number of bill texts to analyze")
    parser.add_argument("--min-words", type=int, default=100, help="Minimum word threshold for bill texts")
    parser.add_argument("--session-year", type=int, help="Filter to a specific session year")
    parser.add_argument("--topics", type=int, default=5, help="Number of LDA topics to compute")
    parser.add_argument(
        "--output",
        type=str,
        help="Optional output path for JSON report (default: reports/bill_text_research_<timestamp>.json)",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    common.configure_logging(args.verbose)
    researcher = BillTextResearcher(
        limit=args.limit,
        min_words=args.min_words,
        session_year=args.session_year,
        topics=args.topics,
    )
    summary = researcher.run()

    if args.output:
        output_dir = common.ensure_report_dir(path=args.output)
        path = output_dir / "bill_text_research.json"
    else:
        path = common.timestamped_filename("bill_text_research")

    common.dump_json(summary, path)
    logger.info("Wrote bill text research report to %s", path)


if __name__ == "__main__":  # pragma: no cover
    main()
