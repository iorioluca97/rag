import os
import re
import statistics
from typing import Dict, List

import pdfplumber

from config.cfg import DEFAULT_KEYWORDS_TO_IGNORE, TOC_KEYWORDS
from config.logger import logger


class TextExtractor:
    def __init__(
        self, path: str, toc_keywords: List = None, keywords_to_ignore: List = None
    ):
        self.path = path
        if not toc_keywords:
            self.toc_keywords = TOC_KEYWORDS
        else:
            self.toc_keywords = toc_keywords

        if not keywords_to_ignore:
            self.keywords_to_ignore = DEFAULT_KEYWORDS_TO_IGNORE
        else:
            self.keywords_to_ignore = keywords_to_ignore
        self.pages = []

        self.service_dir = (
            path.split("/")[-1]
            .split(".pdf")[0]
            .lower()
            .replace("/", "_")
            .replace("\\", "_")
        )

    def extract_useful_metadata(self) -> dict:
        with pdfplumber.open(self.path) as pdf:
            metadata = pdf.metadata
            return metadata

    def find_toc(self, pdf) -> int:
        for page_num, page in enumerate(
            pdf.pages[:10]
        ):  # Limit the search to the first X pages
            text = page.extract_text()

            if text:
                for word in self.toc_keywords:
                    if word.lower() in text.lower():
                        logger.info(f"Possible ToC at page: {page_num + 1}")
                        return page_num + 1

        logger.error("Index not found")

    def extract_text_from_toc(self) -> tuple:
        pages = []
        with pdfplumber.open(self.path) as pdf:
            page_number_index = self.find_toc(pdf)

            # If the index is found, extract the text
            if page_number_index:
                pages.append(page_number_index)
                page_index = pdf.pages[page_number_index - 1]
                index_text = page_index.extract_text()

                # Try to extract more text from the succeeding page
                next_page_index = pdf.pages[page_number_index]
                next_index_text = next_page_index.extract_text()
                pages.append(page_number_index + 1)
        return (index_text, next_index_text, pages)

    def extract_toc_entries(self, text) -> list:
        res = []
        # Regex to find "title ..... page_number"
        patterns = [r"(.+?)\s+\.{2,}\s+(\d+)", r"(.+?)\s+\.{2,}(\d+)"]
        for pattern in patterns:
            index_entries = re.findall(pattern, text)
            if len(index_entries) > 0:
                logger.debug(f"Found {len(index_entries)} entries")
                break
        for entry in index_entries:
            titolo, pagina = entry
            res.append({"title": titolo.strip(), "page": pagina})
        return res

    def generate_toc(self) -> tuple:
        toc = []
        with pdfplumber.open(self.path) as pdf:
            index_toc = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and any(keyword in text for keyword in self.toc_keywords):
                    index_toc.append(
                        i + 1
                    )  # Le pagine in pdfplumber sono 0-indexed, mentre per l'utente sono 1-indexed

                    list_lines = text.split("\n")

                    for line in list_lines:
                        # Remove multiple spaces or dots
                        line = re.sub(r"\s+", " ", line)
                        line = re.sub(r"\.{2,}", "", line)

                        # Extract number title, title name, and page title
                        match = re.match(r"(\d+(?:\.\d+)?)\s+(.+?)\s+(\d+)$", line)
                        if match:
                            main_chapters = match.groups()
                            # Create a toc dictionary
                            toc.append(
                                {
                                    "number": main_chapters[0],
                                    "title": main_chapters[1].strip(),
                                    "page": main_chapters[2],
                                }
                            )
            logger.info(f"Found {len(toc)} entries in the ToC")

            found_additional_toc_entries = False
            if index_toc.__len__() > 0:
                for i, page in enumerate(pdf.pages):
                    # Try to find additional toc in the next page
                    if index_toc[0] + 1 == i:
                        next_page = pdf.pages[i - 1]
                        next_page_text = next_page.extract_text()
                        next_page_lines = next_page_text.split("\n")

                        for next_line in next_page_lines:
                            next_line = re.sub(r"\s+", " ", next_line)
                            next_line = re.sub(r"\.{2,}", "", next_line)
                            next_match = re.match(
                                r"(\d+(?:\.\d+)?)\s+(.+?)\s+(\d+)$", next_line
                            )
                            if next_match:
                                next_chapters = next_match.groups()
                                toc.append(
                                    {
                                        "number": next_chapters[0],
                                        "title": next_chapters[1].strip(),
                                        "page": next_chapters[2],
                                    }
                                )
                                found_additional_toc_entries = True
                                page_index = i

                if found_additional_toc_entries:
                    logger.info("Found additional entries in the next page.")
                    index_toc.append(page_index)
        return (toc, index_toc)

    def extract_full_text(self):
        if os.path.exists("extracted_pages") is False:
            logger.info("Creating directory to store extracted pages.")
            os.mkdir("extracted_pages")
        if os.path.exists(f"extracted_pages/{self.service_dir}") is False:
            os.mkdir(f"extracted_pages/{self.service_dir}")
        with pdfplumber.open(self.path) as pdf:
            complete_text = ""
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                with open(
                    f"extracted_pages/{self.service_dir}/page_{i}.txt",
                    "w",
                    encoding="utf-8",
                ) as file:
                    file.write(page_text or "")
                    file.close()
                complete_text += page_text or ""
        logger.info("Text extracted from all pages")
        return complete_text

    def extract_keywords(self, pages: List[int]) -> dict:
        bold_text = {}

        with pdfplumber.open(self.path) as pdf:
            # Compute global text statistics across all pages
            all_char_sizes = [
                char.get("size", 0) for page in pdf.pages for char in page.chars
            ]

            # Calculate size thresholds
            avg_font_size = statistics.mean(all_char_sizes) if all_char_sizes else 10
            size_threshold = avg_font_size * 1.2

            for page in pdf.pages:
                if (
                    page.page_number not in pages
                ):  # Se la pagina non è una pagina di indice
                    page_chars = []
                    for char in page.chars:
                        if (
                            "Bold" in char.get("fontname", "")
                            or
                            # char.get("stroking_color", None) in significant_colors or
                            char.get("stroking_color", None) != (0,)
                        ) or char.get("size", 0) > size_threshold:
                            page_chars.append(char.get("text", ""))
                    full_text = "".join(page_chars)

                    char_list = [char for char in full_text.split(" ") if char]

                    refactored_char_list = []
                    for char in char_list:
                        for keyword in self.keywords_to_ignore:
                            replaced_char = char.replace(keyword, "")
                            if replaced_char != "":
                                refactored_char_list.append(replaced_char.lower())
                            break
                    unique_chars = list(set(refactored_char_list))
                    unified_chars = " ".join(unique_chars)
                    # Remove punctuation
                    bold_text[page.page_number] = clean_text(unified_chars)

        keywords = {}
        for key, value in bold_text.items():
            values_list = value.split(" ")
            new_value_list = []

            for v in values_list:
                # Check if any keyword to ignore is in the word
                is_ignored = any(
                    keywords_to_ignore in v
                    for keywords_to_ignore in self.keywords_to_ignore
                )

                if is_ignored:
                    # Remove the keywords to ignore and add the cleaned word
                    new_value = v
                    for keywords_to_ignore in self.keywords_to_ignore:
                        new_value = new_value.replace(keywords_to_ignore, "")
                    new_value_list.append(new_value.lower())
                else:
                    # If no keywords to ignore, add the original word
                    new_value_list.append(v.lower())

            # Remove duplicates
            new_value_list = list(set(new_value_list))
            keywords[key - 1] = new_value_list

        # Clean up the keywords
        return clean_keywords(keywords)


def clean_text(text: str) -> str:
    text = (
        text.strip()
        .replace(":", "")
        .replace(",", "")
        .replace(".", "")
        .replace(";", "")
        .replace("’", "")
        .replace("‘", "")
        .replace("(", "")
        .replace(")", "")
    )
    return text


def clean_keywords(keywords: Dict[int, List[str]]) -> Dict[int, List[str]]:
    for key, value in keywords.items():
        for keyword in value:
            if (
                keyword == ""
                or keyword == " "
                or len(keyword) < 2
                or keyword.isdigit()
                or len(keyword) > 15
            ):
                value.remove(keyword)
    return keywords
