import os
from os.path import join, splitext, getmtime, basename
from pathlib import Path
import subprocess

from .ResumeComponents.Resume import Resume
from .Enums.Font import Font
from .Funcs.Funcs import create_and_write_file


class ResumeCompiler:
    """
    This class is responsible for compiling Markdown files into .tex files, then into resume PDFs.
    """

    def __init__(self, src_dir_path: str, dist_dir_path: str):
        """
        :param src_dir_path: The source directory path.
        This directory should contain one or more markdown files to be compiled.
        :param dist_dir_path: The destination directory path.
        After compilation, this directory will contain one or more subdirectories, each corresponding to a Markdown file in the source directory.
        Each subdirectory contains the .tex file, the compiled resume PDF and other log files.
        """
        self.src_dir: str = src_dir_path
        self.dist_dir: str = dist_dir_path

        # A dictionary mapping each source file's path to the timestamp marking its last modification.
        # The timestamp refers to the number of seconds since the epoch, rounded to an integer.
        # This is required for running the compiler with auto-save enabled.
        self.last_modification_timestamps: dict[str, int] = dict()

    def get_paths_to_markdown_files_in_src_dir(self) -> list[str]:
        """
        :return: A list of paths to markdown files in the source directory.
        """
        result = []

        for directory_item in os.listdir(self.src_dir):
            # Ignore non-markdown files
            src_file_extension = splitext(directory_item)[1]

            if src_file_extension == ".md":
                src_file_path: str = join(self.src_dir, directory_item)
                result.append(src_file_path)

        return result

    def compile(self, src_file_path: str, font: Font = Font.TIMES_NEW_ROMAN):
        """
        Compiles a specific Markdown file to PDF.
        :param src_file_path: The path to the source markdown file to be compiled.
        :param font: The font to use for the compiled resume.
        :return:
        """
        src_file_name: str = splitext(basename(src_file_path))[0]

        resume: Resume = get_resume_object_from_markdown(src_file_path)

        # Try to compile the Markdown file to LaTeX
        try:
            latex_lines: list[str] = resume.to_latex_lines(font)
            latex_result: str = "\n".join(latex_lines)
        except (Exception, IndexError) as e:
            print("MARKDOWN TO LATEX COMPILATION FAILED. ERROR:", e)
            return

        # Create and write to a destination file located in a subdirectory of the same name
        dest_file_path: Path = Path(self.dist_dir, src_file_name, src_file_name + ".tex")
        create_and_write_file(dest_file_path, latex_result)

        # Compile latex to pdf
        compile_latex_file_to_pdf(dest_file_path)


    def run(self, font: Font = Font.TIMES_NEW_ROMAN):
        """
        :return: Compiles all Markdown files in the source directory and saves the outputs in the destination directory.
        """
        for src_file_path in self.get_paths_to_markdown_files_in_src_dir():
            self.compile(src_file_path, font)

    def run_with_live_reload(self, font: Font = Font.TIMES_NEW_ROMAN):
        """
        :return: Runs a loop so that whenever a Markdown file in the source directory is created or saved, it is compiled with the outputs saved in the destination directory.
        """
        while True:
            for src_file_path in self.get_paths_to_markdown_files_in_src_dir():
                last_modification_timestamp_recorded = self.last_modification_timestamps.get(src_file_path, -1)
                last_modification_timestamp_of_file = round(getmtime(src_file_path))

                if last_modification_timestamp_of_file == last_modification_timestamp_recorded:
                    continue

                self.last_modification_timestamps[src_file_path] = last_modification_timestamp_of_file
                self.compile(src_file_path, font)



def get_resume_object_from_markdown(src_file_path: str) -> Resume:
    """
    :param src_file_path: The path to the source Markdown file from which the Resume object is to be read.
    :return: A Resume object.
    """
    with open(src_file_path, "r", encoding="utf-8") as markdown_file:
        return Resume(markdown_file.read())


def compile_latex_file_to_pdf(latex_file_path: Path, print_stdout_and_stderr: bool = True):
    """
    :param latex_file_path: The path to the LaTeX file.
    :param print_stdout_and_stderr: Whether to print the stdout and stderr messages to the console.
    :return: Compiles the specified LaTeX file to PDF, optionally printing stdout and stderr messages to the console.
    """
    # Change our working directory to where the destination tex file was created, then compile it to pdf
    parent_directory_of_latex_file = latex_file_path.parent.as_posix()

    process = subprocess.Popen(
        ['pdflatex', latex_file_path.name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        text=True,
        cwd=parent_directory_of_latex_file
    )

    if print_stdout_and_stderr:
        # Capture and print the output
        stdout, stderr = process.communicate()

        # Print the output for debugging
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)
