from enum import StrEnum
class NewsletterStatus(StrEnum):
    DRAFT="DRAFT"; READY_FOR_REVIEW="READY_FOR_REVIEW"; APPROVED="APPROVED"; REJECTED="REJECTED"; SCHEDULED="SCHEDULED"; SENT="SENT"; FAILED="FAILED"
class SourceType(StrEnum):
    RSS="rss"; REDDIT="reddit"; HACKER_NEWS="hacker_news"; CROSSREF="crossref"; FRED="fred"; GDELT="gdelt"; FIXTURE="fixture"
