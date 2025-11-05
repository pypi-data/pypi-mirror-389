from bs4 import Tag

from resumecompiler.ResumeComponents.OrganisationalSectionResumeItem import OrganisationalSectionResumeItem
from resumecompiler.ResumeComponents.ResumeSection import ResumeSection, get_toolset_or_organisational_section_as_latex_lines, classify_tags_in_organisational_or_toolset_section_by_resume_item


class OrganisationalSection(ResumeSection):
    def __init__(self, tags: list[Tag]):
        """
        :param tags: A list of HTML tags that belong to this organisational section.
        """
        h2_tag: Tag = tags.pop(0)
        heading: str = h2_tag.text

        super().__init__(heading=heading)

        tags_by_resume_item: list[list[Tag]] = classify_tags_in_organisational_or_toolset_section_by_resume_item(tags)

        # Initialise resume items
        self.resume_items: list[OrganisationalSectionResumeItem] = [
            OrganisationalSectionResumeItem(tags_for_resume_item) for tags_for_resume_item in tags_by_resume_item
        ]

    def to_latex_lines(self) -> list[str]:
        return get_toolset_or_organisational_section_as_latex_lines(heading=self.heading, resume_items=self.resume_items)
