package gov.nysenate.openleg.ingestion.model;

import java.util.List;

public class GovinfoBill {
    public String billNumber;
    public String billType;
    public String title;
    public List<Title> titles;
    public String originChamber;
    public List<Action> actions;
    public List<Sponsor> sponsors;
    public List<Cosponsor> cosponsors;
    public CommitteeInfo committees;
    public Summaries summaries;
    public String latestAction;
    public String introducedDate;
    public String congress;
    public List<TextVersion> textVersions;

    public static class Title {
        public String titleType;
        public String chamberCode;
        public String chamberName;
        public String title;
    }

    public static class Action {
        public String actionDate;
        public String text;
        public String type;
        public String actionCode;
        public SourceSystem sourceSystem;
        public List<Committee> links;
    }

    public static class SourceSystem {
        public int code;
        public String name;
    }

    public static class Sponsor {
        public String bioguideId;
        public String fullName;
        public String firstName;
        public String middleName;
        public String lastName;
    }

    public static class Cosponsor {
        public String bioguideId;
        public String fullName;
        public String firstName;
        public String middleName;
        public String lastName;
        public boolean isOriginalCosponsor;
    }

    public static class CommitteeInfo {
        public List<CommitteeItem> billCommittees;
    }

    public static class CommitteeItem {
        public String chamber;
        public String name;
        public String systemCode;
        public List<Activity> activities;
        public List<Subcommittee> subcommittees;
    }

    public static class Activity {
        public String name;
        public String date;
    }

    public static class Subcommittee {
        public String chamber;
        public String name;
        public String systemCode;
        public List<Activity> activities;
    }

    public static class Summaries {
        public List<SummaryItem> billSummaries;
    }

    public static class SummaryItem {
        public String text;
        public String name;
        public String actionDate;
        public String actionDesc;
        public String updateDate;
        public String versionCode;
    }

    public static class Committee {
        public String systemCode;
        public String name;
    }

    public static class TextVersion {
        public String type;
        public String date;
        public List<Format> formats;
    }

    public static class Format {
        public String url;
    }
}