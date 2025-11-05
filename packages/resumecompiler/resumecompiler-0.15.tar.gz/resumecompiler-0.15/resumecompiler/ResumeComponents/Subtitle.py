from bs4.element import Tag

from resumecompiler.ResumeComponents.ResumeComponent import ResumeComponent
from resumecompiler.Funcs.LatexFuncs import get_latex_environment, get_latex_command


class Subtitle(ResumeComponent):
    def __init__(self, pre_tag: Tag):
        """
        :param pre_tag: The <pre> HTML tag representing this title.
        """
        super().__init__()
        self.text = pre_tag.text

    def to_latex_lines(self) -> list[str]:
        return get_latex_environment(
            env="center",
            contents=[
                get_latex_command(
                    command="textbf",
                    arguments=[self.text]
                )
            ]
        )
