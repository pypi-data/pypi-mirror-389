from bs4 import Tag

from resumecompiler.ResumeComponents.ResumeSection import ResumeSection
from resumecompiler.Funcs.HtmlFuncs import get_children_tags
from resumecompiler.Funcs.LatexFuncs import get_latex_command


class CatalogueSection(ResumeSection):
    def __init__(self, tags: list[Tag]):
        """
        :param tags: A list of HTML tags that belong to this catalogue section.
        """
        h2_tag = tags.pop(0)
        heading: str = h2_tag.text
        super().__init__(heading=heading)

        # Initialise the list under this catalogue section
        self.catalogue_list = []
        for tag in tags:
            if tag.name == "ul":
                for children_tag in get_children_tags(tag):
                    if children_tag.name == "li":
                        self.catalogue_list.append(children_tag.text)

    def to_latex_lines(self) -> list[str]:
        result = [get_latex_command("section", [self.heading])]

        if not self.catalogue_list:
            return result

        result.append("")
        result.append(r"\begin{itemize}[leftmargin=0.15in, label={}, itemsep=-2pt]\small")

        # Detect and parse labels in each list item
        # [Label]: [thing], [thing], ...
        for list_item in self.catalogue_list:
            if ":" in list_item:
                label, text = list_item.split(":", maxsplit=1)
                latex_line = get_latex_command(command="textbf", arguments=[label]) + ":" + text
            else:
                latex_line = list_item
            result.append("\t\item" + latex_line + r"\\")

        result.append(r"\end{itemize}")

        return result