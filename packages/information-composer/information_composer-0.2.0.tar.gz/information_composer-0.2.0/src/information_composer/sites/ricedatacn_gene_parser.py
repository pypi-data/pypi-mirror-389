"""Parser module for extracting gene information from ricedata.cn.

This module provides functionality to parse gene information from the RiceDataCN
website, including basic gene information, ontology data, and references.
"""

import json
import os
import re
import traceback
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, Tag
import requests

from information_composer.sites.base import BaseSiteCollector


class RiceGeneParser(BaseSiteCollector):
    """Parser for extracting gene information from ricedata.cn.

    This class provides methods to parse gene information from the RiceDataCN
    website, including basic gene information, ontology data, and references.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the RiceGeneParser.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.base_url = "https://www.ricedata.cn/gene/list"

    def collect(self) -> Any:
        """Collect gene information (not implemented for this parser).

        This method is not used for this parser as it requires specific gene IDs.
        Use parse_gene_page or parse_multiple_genes instead.

        Returns:
            None

        Raises:
            NotImplementedError: This method is not implemented for this parser
        """
        raise NotImplementedError("Use parse_gene_page or parse_multiple_genes instead")

    def compose(self, data: Any) -> Any:
        """Compose collected data (not implemented for this parser).

        Args:
            data: The data to compose

        Returns:
            The composed data

        Raises:
            NotImplementedError: This method is not implemented for this parser
        """
        raise NotImplementedError("Use parse_gene_page or parse_multiple_genes instead")

    def parse_gene_page(
        self, gene_id: str, output_dir: str = "downloads/genes"
    ) -> Optional[Dict[str, Any]]:
        """Parse gene information from ricedata.cn webpage.

        Args:
            gene_id: The gene ID to parse
            output_dir: Directory to save the output file

        Returns:
            Dictionary containing parsed gene information, or None if parsing failed
        """
        url = f"{self.base_url}/{gene_id}.htm"

        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Get webpage content
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = "gb2312"  # Gene pages use GB2312 encoding

            soup = BeautifulSoup(response.text, "html.parser")

            # Get basic reference information
            references = self._parse_references(soup)

            # Get detailed information for each reference
            for ref in references:
                if "reference_url" in ref:
                    ref_url = ref["reference_url"]
                    if not ref_url.startswith("http"):
                        ref_url = f"https://www.ricedata.cn/{ref_url.lstrip('/')}"
                    print(f"Getting details for {ref_url}")
                    details = self._get_reference_details(ref_url)
                    ref.update(details)

            gene_info = {
                "gene_id": gene_id,
                "url": url,
                "basic_info": self._parse_basic_info(soup),
                "description": self._parse_gene_description(soup),
                "ontology": self._parse_ontology(soup),
                "references": references,
            }

            # Save to JSON file
            output_file = os.path.join(output_dir, f"gene_{gene_id}.json")
            self._save_to_json(gene_info, output_file)

            return gene_info

        except requests.exceptions.HTTPError as e:
            if (
                hasattr(e, "response")
                and e.response is not None
                and e.response.status_code == 404
            ):
                print(f"Gene ID {gene_id} not found (404 error)")
                return None
            raise
        except Exception as e:
            print(f"Error parsing gene page: {e!s}")
            traceback.print_exc()
            return None

    def parse_multiple_genes(
        self, gene_ids: List[str], output_dir: str = "downloads/genes"
    ) -> List[Optional[Dict[str, Any]]]:
        """Parse multiple genes and save their information.

        Args:
            gene_ids: List of gene IDs to parse
            output_dir: Directory to save the JSON files

        Returns:
            List of parsed gene information dictionaries
        """
        results = []
        for gene_id in gene_ids:
            print(f"\nParsing gene ID: {gene_id}")
            gene_info = self.parse_gene_page(gene_id, output_dir)
            results.append(gene_info)
        return results

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.

        Args:
            text: The text to clean

        Returns:
            Cleaned text
        """
        if text is None:
            return ""

        # Remove special characters and normalize spaces
        text = text.replace("：", "").replace(":", "")
        text = re.sub(r"\s+", " ", text)
        # Remove any potential BOM or special characters
        text = text.replace("\ufeff", "")
        return text.strip()

    def _parse_basic_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Parse basic gene information from the first table.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Dictionary containing basic gene information
        """
        basic_info: Dict[str, str] = {}
        tables = soup.find_all("table")
        if not tables:
            return basic_info

        table = tables[0]
        if not isinstance(table, Tag):
            return basic_info
        rows = table.find_all("tr")

        current_key = None
        current_value = []

        for row in rows:
            if not isinstance(row, Tag):
                continue
            cols = row.find_all("td")
            if len(cols) >= 2:
                # Get the text content
                key_text = self._clean_text(cols[0].get_text(strip=True))
                value_text = self._clean_text(cols[1].get_text(strip=True))

                # If it's a new key
                if key_text:
                    # Save previous key-value pair if exists
                    if current_key and current_value:
                        basic_info[current_key] = " ".join(current_value)
                    # Start new key-value pair
                    current_key = key_text
                    current_value = [value_text]
                else:
                    # Append to current value if it's a continuation
                    if current_key and value_text:
                        current_value.append(value_text)

        # Save the last key-value pair
        if current_key and current_value:
            basic_info[current_key] = " ".join(current_value)

        return basic_info

    def _parse_ontology(self, soup: BeautifulSoup) -> Dict[str, List[Dict[str, str]]]:
        """Parse gene ontology information from the second table.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Dictionary containing ontology information
        """
        ontology: Dict[str, List[Dict[str, str]]] = {}
        tables = soup.find_all("table")
        if len(tables) < 2:
            return ontology

        table = tables[1]
        if not isinstance(table, Tag):
            return ontology
        rows = table.find_all("tr")

        for row in rows:
            if not isinstance(row, Tag):
                continue
            cols = row.find_all("td")
            if len(cols) >= 2:
                key = self._clean_text(cols[0].get_text(strip=True))

                # Extract ontology terms and their links
                terms = []
                if not isinstance(cols[1], Tag):
                    continue
                links = cols[1].find_all("a")
                for link in links:
                    href = link.get("href", "") if hasattr(link, "get") else ""
                    if isinstance(href, str):
                        href_id = href.split("=")[-1]
                    else:
                        href_id = ""
                    terms.append(
                        {
                            "term": self._clean_text(link.get_text(strip=True)),
                            "id": href_id,
                        }
                    )

                if key and terms:
                    ontology[key] = terms

        return ontology

    def _parse_gene_description(self, soup: BeautifulSoup) -> str:
        """Parse gene description from the content cell.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Gene description text
        """
        try:
            # Find the content cell with colspan=2
            content_cell = soup.find(
                "td", attrs={"colspan": "2", "style": "padding: 5px; font-size: 14px"}
            )
            if not content_cell or not isinstance(content_cell, Tag):
                return ""

            # Get all description text, including titles
            description_text = []

            # Get red text part (locus information)
            red_text = content_cell.find(
                "p", style="color: rgb(255, 0, 0); font-weight: bold"
            )
            if red_text:
                description_text.append(red_text.get_text(strip=True))

            # Get all h5 titles and corresponding paragraphs
            current_section = None
            for element in content_cell.children:
                if not isinstance(element, Tag):
                    continue
                if element.name == "h5":
                    current_section = element.get_text(strip=True)
                    description_text.append(f"\n{current_section}")
                elif element.name == "p":
                    # Remove HTML tags but preserve text format
                    text = element.get_text(strip=True)
                    if text:
                        description_text.append(text)

            # Filter out the "【相关登录号】" section
            filtered_text = []
            for text in description_text:
                if "【相关登录号】" not in text:
                    filtered_text.append(text)

            # Combine all text with newlines
            return "\n".join(filtered_text)

        except Exception as e:
            print(f"Error parsing gene description: {e!s}")
            return ""

    def _parse_references(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parse reference information from the reference table.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            List of reference dictionaries
        """
        references = []

        try:
            # Find all reference table rows
            ref_rows = soup.find_all(
                "td",
                style=lambda x: x
                and (
                    "BACKGROUND-COLOR:#eef9de" in x or "BACKGROUND-COLOR:#ffffcc" in x
                ),
            )

            for row in ref_rows:
                # Get link and text
                if not isinstance(row, Tag):
                    continue
                link = row.find("a")
                if not link or not isinstance(link, Tag):
                    continue

                # Fix URL construction
                href = link.get("href")
                if not href or not isinstance(href, str):
                    continue
                url = "https://www.ricedata.cn/" + href.replace("../../", "")

                # Extract complete reference text
                text_parts = []
                for content in row.stripped_strings:
                    if content not in [".", "(", ")", ":"]:
                        text_parts.append(content)

                reference_info = " ".join(text_parts[1:])  # Skip sequence number

                reference = {"reference_info": reference_info, "reference_url": url}
                references.append(reference)

            print(f"Found {len(references)} references")

        except Exception as e:
            print(f"Error parsing references: {e!s}")
            traceback.print_exc()

        return references

    def _get_reference_details(self, ref_url: str) -> Dict[str, str]:
        """Get detailed information for a reference.

        Args:
            ref_url: URL of the reference

        Returns:
            Dictionary containing reference details
        """
        try:
            if ref_url.startswith("@"):
                ref_url = ref_url[1:]

            if not ref_url.startswith("http"):
                ref_url = f"https://www.ricedata.cn/{ref_url}"

            response = requests.get(ref_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            details = {}

            # Get title
            title = soup.find("h1")
            if title:
                details["title"] = title.get_text(strip=True)

            # Get DOI
            h5_elements = soup.find_all("h5")
            for h5 in h5_elements:
                if "DOI:" in h5.get_text():
                    doi_text = h5.get_text()
                    doi_match = re.search(
                        r"DOI:\s*(10\.\d{4,}/[-._;()/:\w]+)", doi_text
                    )
                    if doi_match:
                        details["doi"] = doi_match.group(1)
                    break

            # Get English abstract
            en_p = soup.find(
                "p", style=lambda x: x and "margin" in x and "margin-bottom:10" in x
            )
            if en_p:
                details["abstract_en"] = en_p.get_text(strip=True)

            # Get Chinese abstract
            cn_title = soup.find("h1", style=lambda x: x and "color: orangered" in x)
            if cn_title:
                cn_p = cn_title.find_next("p")
                if cn_p and isinstance(cn_p, Tag):
                    # Preserve line breaks and indentation
                    text_parts = []
                    for element in cn_p.children:
                        if not isinstance(element, Tag):
                            continue
                        if element.name == "br":
                            text_parts.append("\n")
                        elif (
                            element.name == "em"
                            or element.name == "sup"
                            or element.name == "sub"
                        ):
                            text_parts.append(element.get_text())
                        else:
                            # Handle other element types
                            try:
                                text = str(element).replace("&emsp;", "    ")
                                text_parts.append(text)
                            except Exception:
                                # Fallback to basic string conversion
                                text_parts.append(str(element))

                    details["abstract_cn"] = "".join(text_parts).strip()

            return details

        except Exception as e:
            print(f"Error getting reference details from {ref_url}: {e!s}")
            traceback.print_exc()
            return {}

    def _save_to_json(self, data: Dict[str, Any], output_file: str) -> None:
        """Save parsed data to JSON file.

        Args:
            data: Data to save
            output_file: Output file path
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Data saved to: {output_file}")
        except Exception as e:
            print(f"Error saving to JSON: {e!s}")
