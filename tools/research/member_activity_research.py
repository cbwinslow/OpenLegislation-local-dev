"""Member activity and tenure research for federal legislators."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from psycopg2 import errors, sql

from . import common

logger = logging.getLogger(__name__)


@dataclass
class MemberTerm:
    member_id: int
    full_name: str
    chamber: str
    state: Optional[str]
    party: Optional[str]
    congress: Optional[int]
    start_year: Optional[int]
    end_year: Optional[int]
    current_member: bool


class MemberActivityResearcher:
    """Generate tenure and activity insights for federal legislators."""

    def __init__(self, include_historical: bool = True) -> None:
        self.include_historical = include_historical

    def fetch_member_terms(self) -> List[MemberTerm]:
        query = sql.SQL(
            """
            SELECT
                m.id AS member_id,
                p.full_name,
                m.chamber,
                m.state,
                m.party,
                t.congress,
                t.start_year,
                t.end_year,
                m.current_member
            FROM master.federal_member AS m
            JOIN master.federal_person AS p ON p.id = m.person_id
            LEFT JOIN master.federal_member_term AS t ON t.member_id = m.id
            {historical_filter}
            ORDER BY p.full_name ASC
            """
        ).format(
            historical_filter=sql.SQL("")
            if self.include_historical
            else sql.SQL("WHERE m.current_member = true")
        )

        try:
            with common.db_cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
        except errors.UndefinedTable:
            logger.warning(
                "Federal member tables missing; returning empty dataset. Ensure migrations have been applied."
            )
            rows = []

        terms = [
            MemberTerm(
                member_id=row["member_id"],
                full_name=row["full_name"],
                chamber=row["chamber"],
                state=row.get("state"),
                party=row.get("party"),
                congress=row.get("congress"),
                start_year=row.get("start_year"),
                end_year=row.get("end_year"),
                current_member=row["current_member"],
            )
            for row in rows
        ]
        logger.info("Loaded %s member term records", len(terms))
        return terms

    @staticmethod
    def build_dataframe(terms: List[MemberTerm]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "member_id": term.member_id,
                    "full_name": term.full_name,
                    "chamber": term.chamber,
                    "state": term.state,
                    "party": term.party,
                    "congress": term.congress,
                    "start_year": term.start_year,
                    "end_year": term.end_year,
                    "current_member": term.current_member,
                }
                for term in terms
            ]
        )

    @staticmethod
    def compute_tenure(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        current_year = datetime.utcnow().year
        df = df.copy()
        df["start_year"].fillna(df["end_year"], inplace=True)
        df["end_year"].fillna(df["start_year"], inplace=True)
        df["start_year"].fillna(current_year, inplace=True)
        df["end_year"].fillna(current_year, inplace=True)
        df["tenure_years"] = (
            df["end_year"].clip(upper=current_year) - df["start_year"].clip(upper=current_year) + 1
        ).clip(lower=0)
        return df

    def summarize_current_members(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {}
        current = df[df["current_member"]].drop_duplicates(subset=["member_id"])
        totals = (
            current.groupby(["chamber", "party"], dropna=False)["member_id"].nunique().reset_index()
        )
        return {
            "by_chamber_party": totals.to_dict(orient="records"),
            "total_current": int(current["member_id"].nunique()),
        }

    def summarize_tenure(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {}
        tenure = df.groupby("member_id")["tenure_years"].sum().reset_index()
        merged = tenure.merge(df.drop_duplicates(subset=["member_id"]), on="member_id", how="left")
        stats = {
            "mean_years": float(tenure["tenure_years"].mean()),
            "median_years": float(tenure["tenure_years"].median()),
            "max_years": float(tenure["tenure_years"].max()),
            "min_years": float(tenure["tenure_years"].min()),
        }
        top = merged.sort_values("tenure_years", ascending=False).head(10)
        return {
            "stats": stats,
            "longest_serving": top[["full_name", "chamber", "party", "state", "tenure_years"]].to_dict(
                orient="records"
            ),
        }

    def summarize_freshmen(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if df.empty:
            return []
        current_year = datetime.utcnow().year
        cutoff = current_year - 2
        first_terms = (
            df[df["current_member"]]
            .groupby("member_id")
            .agg(first_year=("start_year", "min"), full_name=("full_name", "first"), chamber=("chamber", "first"), party=("party", "first"), state=("state", "first"))
            .reset_index()
        )
        freshmen = first_terms[first_terms["first_year"] >= cutoff]
        return freshmen.sort_values("first_year").to_dict(orient="records")

    def run(self) -> Dict[str, Any]:
        terms = self.fetch_member_terms()
        df = self.build_dataframe(terms)
        df = self.compute_tenure(df)

        current_summary = self.summarize_current_members(df)
        tenure_summary = self.summarize_tenure(df)
        freshmen = self.summarize_freshmen(df)

        summary = {
            "metadata": {
                "include_historical": self.include_historical,
                "records": len(df),
            },
            "current_members": current_summary,
            "tenure": tenure_summary,
            "freshmen": freshmen,
            "records": df.to_dict(orient="records"),
        }
        return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Member activity and tenure research")
    parser.add_argument(
        "--historical",
        dest="include_historical",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Include historical members (default true; use --no-historical for current only)",
    )
    parser.add_argument("--output", help="Directory to write JSON report into")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    common.configure_logging(args.verbose)
    researcher = MemberActivityResearcher(include_historical=args.include_historical)
    summary = researcher.run()

    if args.output:
        output_dir = common.ensure_report_dir(path=args.output)
        path = output_dir / "member_activity_research.json"
    else:
        path = common.timestamped_filename("member_activity_research")

    common.dump_json(summary, path)
    logger.info("Wrote member activity research report to %s", path)


if __name__ == "__main__":  # pragma: no cover
    main()
