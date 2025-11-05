from bs4 import BeautifulSoup
from bs4.element import Tag

from pathlib import Path
import re

from resumecompiler.ResumeComponents.CatalogueSection import CatalogueSection
from resumecompiler.ResumeComponents.ResumeComponent import ResumeComponent
from resumecompiler.ResumeComponents.OrganisationalSection import OrganisationalSection
from resumecompiler.ResumeComponents.Subtitle import Subtitle
from resumecompiler.ResumeComponents.Title import Title
from resumecompiler.ResumeComponents.ContactList import ContactList
from resumecompiler.ResumeComponents.ResumeSection import ResumeSection
from resumecompiler.ResumeComponents.ToolsetSection import ToolsetSection
from resumecompiler.Funcs.HtmlFuncs import get_soup_from_markdown, get_children_tags
from resumecompiler.Funcs.LatexFuncs import get_latex_environment
from resumecompiler.Enums.Font import Font


PREAMBLE_TEX_FILE_NAME: str = "preamble.tex"  # Should be located in the same directory as this file


class Resume(ResumeComponent):
    def __init__(self, markdown_contents: str):
        """
        :param markdown_contents: The Markdown content to be compiled.
        """
        super().__init__()

        soup: BeautifulSoup = get_soup_from_markdown(markdown_contents)
        tags: list[Tag] = get_children_tags(soup)

        tags = process_hidden_elements(tags)

        num_of_tags: int = len(tags)

        # Categorise tags by section
        i: int = 0
        tags_prior_to_first_section: list[Tag] = []
        tags_by_section: list[list[Tag]] = []

        while i < num_of_tags and tags[i].name != "h2":
            tags_prior_to_first_section.append(tags[i])
            i += 1

        while i < num_of_tags:
            if tags[i].name == "h2":
                tags_by_section.append([tags[i]])
            else:
                tags_by_section[-1].append(tags[i])
            i += 1

        # Parse components
        self.components: list[ResumeComponent] = []  # Contains Title, Subtitle, ContactList and ResumeSection objects

        for tag in tags_prior_to_first_section:
            if tag.name == "h1":  # Title
                self.components.append(Title(tag))
            elif tag.name == "pre":
                self.components.append(Subtitle(tag))
            elif tag.name == "ul":  # Contact list
                self.components.append(ContactList(tag))

        for tags_in_section in tags_by_section:
            self.components.append(get_resume_section_from_tags(tags_in_section))

    def to_latex_lines(self, font: Font = Font.TIMES_NEW_ROMAN) -> list[str]:
        result: list[str] = []

        # Preamble
        with open(Path(__file__).parent.joinpath(PREAMBLE_TEX_FILE_NAME), "r") as preamble_file:
            for line in preamble_file:
                line = line.removesuffix('\n')

                if line == "% FONT CHOICE GOES HERE":
                    line = font.value

                result.append(line)

        result.append("")

        # Main body
        document_contents: list[str] = []
        for component in self.components:
            document_contents += component.to_latex_lines()
            for _ in range(3):
                document_contents.append("")

        result += get_latex_environment(env="document", contents=document_contents, indent_contents=False)

        return result


def process_hidden_elements(tags: list[Tag]) -> list[Tag]:
    """
    :param tags: A list of tags obtained from the BeautifulSoup object as parsed from the input Markdown file.
    :return: A processed version of that list where hidden sections, items and descriptions have been removed.
    """
    result: list[Tag] = []

    # These booleans indicate, as we iterate through the following FOR loop,
    # whether we are currently in the scope of a hidden h2 or h3 heading.
    # An h2 heading's scope starts with that heading and ends with the element immediately before the next h2 heading.
    # An h3 heading's scope starts with that heading and ends with the element immediately before the next h2 or h3 heading.
    in_scope_of_hidden_h2_heading: bool = False
    in_scope_of_hidden_h3_heading: bool = False

    for i, tag in enumerate(tags):
        if tag.name == "h2":
            in_scope_of_hidden_h2_heading = tag.text.startswith("^")
            in_scope_of_hidden_h3_heading = False
        elif tag.name == "h3":
            in_scope_of_hidden_h3_heading = tag.text.startswith("^")

        if in_scope_of_hidden_h2_heading or in_scope_of_hidden_h3_heading:
            continue  # If this tag should be hidden, don't include it in the result

        # For unordered lists, we check for any hidden list items
        if tag.name == "ul":
            for li_tag in tag.find_all("li"):
                if li_tag.text.startswith("^"):
                    li_tag.extract()

            if tag.find("li"):  # Some list items still remain
                result.append(tag)
        else:
            result.append(tag)

    return result


def get_resume_section_from_tags(tags: list[Tag]) -> ResumeSection:
    """
    :param tags: A list of HTML tags that belong to a resume section.
    :return: The parsed resume section to which the inputted tags belong.
    """
    # Identify the section type
    heading = tags[0].text

    if len(heading) and heading[0] == "!":
        return ToolsetSection(tags)
    elif any(map(lambda t: t.name == "h3", tags)):
        return OrganisationalSection(tags)
    else:
        return CatalogueSection(tags)