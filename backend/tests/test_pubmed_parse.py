"""Regression: PubMed XML parsing must tolerate records without ELocationID/DOI."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from app.providers.literature.pubmed import _parse_article

NSATT = {"ns": "https://example.invalid/pubmed"}


def _article(xml: str) -> ET.Element:
    return ET.fromstring(xml)


def test_no_elocation_does_not_crash():
    """A valid abstract-bearing article with no ELocationID must parse with doi=None."""
    xml = """<PubmedArticle><MedlineCitation><PMID>123456</PMID>
      <Article>
        <Journal><Title>J Test</Title><JournalIssue><PubDate><Year>2021</Year></PubDate></JournalIssue></Journal>
        <ArticleTitle>A title</ArticleTitle>
        <Abstract><AbstractText>Some abstract text here.</AbstractText></Abstract>
        <PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList>
        <AuthorList><Author><LastName>Doe</LastName><Initials>J</Initials></Author></AuthorList>
      </Article></MedlineCitation></PubmedArticle>"""
    paper = _parse_article(_article(xml), "", "123456")
    assert paper is not None
    assert paper.doi is None  # no crash, no bogus doi
    assert paper.abstract  # abstract retained as evidence


def test_doi_elocation_is_read():
    """An ELocationID with EIdType=doi must populate paper.doi."""
    xml = """<PubmedArticle><MedlineCitation><PMID>98765</PMID>
      <Article>
        <Journal><Title>J Test</Title><JournalIssue><PubDate><Year>2022</Year></PubDate></JournalIssue></Journal>
        <ArticleTitle>B title</ArticleTitle>
        <Abstract><AbstractText>Another abstract.</AbstractText></Abstract>
        <ELocationID EIdType="doi">10.1234/abc.9876</ELocationID>
        <PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList>
        <AuthorList><Author><LastName>Lee</LastName><Initials>S</Initials></Author></AuthorList>
      </Article></MedlineCitation></PubmedArticle>"""
    paper = _parse_article(_article(xml), "", "98765")
    assert paper is not None
    assert paper.doi == "10.1234/abc.9876"


def test_blocked_publication_types_are_skipped():
    xml = """<PubmedArticle><MedlineCitation><PMID>555</PMID>
      <Article>
        <Journal><Title>J</Title><JournalIssue><PubDate><Year>2023</Year></PubDate></JournalIssue></Journal>
        <ArticleTitle>A comment</ArticleTitle>
        <Abstract><AbstractText>Body.</AbstractText></Abstract>
        <PublicationTypeList><PublicationType>Comment</PublicationType></PublicationTypeList>
      </Article></MedlineCitation></PubmedArticle>"""
    assert _parse_article(_article(xml), "", "555") is None


def test_missing_abstract_is_skipped():
    xml = """<PubmedArticle><MedlineCitation><PMID>556</PMID>
      <Article>
        <Journal><Title>J</Title><JournalIssue><PubDate><Year>2023</Year></PubDate></JournalIssue></Journal>
        <ArticleTitle>No abstract</ArticleTitle>
        <PublicationTypeList><PublicationType>Journal Article</PublicationType></PublicationTypeList>
      </Article></MedlineCitation></PubmedArticle>"""
    assert _parse_article(_article(xml), "", "556") is None