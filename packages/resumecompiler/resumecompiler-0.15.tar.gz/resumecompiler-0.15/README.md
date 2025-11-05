# Resume Compiler

A compiler that compiles Markdown files into a resume PDF file, formatted in LaTeX.

Resumes outputted by this compiler will follow the structure given by the ["Jake's Resume" template](https://www.overleaf.com/latex/templates/jakes-resume/syzfjbzwjncs).


## Installation

The compiler is available as a [Python package on PyPI](https://pypi.org/project/resumecompiler/). To install the compiler through ```pip```, simply run the following terminal command.

```aiignore
pip install resumecompiler
```


## Terminology

This section introduces several terms (in bold) used throughout this project and its documentation. The ["Jake's Resume" template](https://www.overleaf.com/latex/templates/jakes-resume/syzfjbzwjncs) is used as an example.

A resume begins with a **title** stating the candidate's first and last name, e.g. ```Jake Ryan```.

There may also be a **subtitle**, a brief line describing the candidate.

Below that is a **contact list**, which provides the candidate's contact details, e.g.
```
123-456-7890 | jake@su.edu | ... | github.com/jake
```

In a resume, all achievements, projects and skills are categorised into separate **sections**. Each section is marked with a **heading**, such as ```Education```, ```Experience```, ```Projects``` or ```Technical Skills```.

There are 3 types of sections:

  - **A toolset section**
  - **An organisational section**
  - **A catalogue section**

A toolset section contains a list of **resume items**, each of which includes:
- a **subheading** describing the achievement (e.g. ```Gitlytics```),
- a **toolset** listing the tools involved (e.g. ```Python, Flask, ...```)
- the time and duration thereof, and
- a **description list**, which is a collection of sentences detailing the achievement (e.g. ```Developed a full-stack web application...```).

A resume item in a toolset section is formatted like this:
```aiignore
Gitlytics | Python, Flask, React...     June 2020 – Present

• Description list item #1
• Description list item #2
```

An organisational section also has a list of resume items. Each resume item in an organisational section contains:
- a subheading describing the achievement (e.g. ```Undergraduate Research Assistant```),
- the time, organisation and location associated therewith, and
- a description list (e.g. ```Developed a REST API using...```).

A resume item in an organisational section is formatted like this:

```aiignore
Undergraduate Research Assistant     June 2020 – Present
Texas A&M University                 College Station, TX

• Description list item #1
• Description list item #2
```

A catalogue section does not contain any resume items. Instead, it displays a simple unordered list, formatted like this:

```aiignore
• Languages: Java, Python, C/C++, SQL (Postgres), JavaScript, HTML/CSS, R
• Frameworks: React, Node.js, Flask, JUnit, WordPress, Material-UI, FastAPI
• Developer Tools: Git, Docker, TravisCI, Google Cloud Platform, VS Code, Visual Studio, PyCharm, IntelliJ, Eclipse
• Libraries: pandas, NumPy, Matplotlib
```

In the above example, the text before each colon (```Languages```, ```Frameworks```, etc.) are called labels and are formatted in bold.



## Syntax

### Create a title, subtitle and contact list

Use an H1 line to create a title.

```aiignore
# Jake Ryan
```

Use a preformatted block to create a subtitle.

```aiignore
    A brief subtitle
```

Use an unordered list to create a contact list. Contacts may include hyperlinks.

```aiignore
# Jake Ryan
- 123-456-7890
- jake@su.edu
- [resume-compiler.com](resume-compiler.com)
```

The title, subtitle and contact list must precede the first section.


### Create an organisational section

Use an H2 heading to create a new section.

```aiignore
## Education
```

Add an H3 subheading for each resume item. Use an indented preformatted code block to add 3 lines of auxiliary information.

```aiignore
### Undergraduate Research Assistant 
    June 2020 - Present
    Texas A&M University
    College Station, TX
```

The subheading and auxiliary information will appear from left to right and from top to bottom in the compiled document.

Then, use an unordered list to create a description list.

```aiignore
### Undergraduate Research Assistant 
    June 2020 - Present
    Texas A&M University
    College Station, TX

- Description list item #1
- Description list item #2
```


### Create a toolset section

Use an H2 heading to create a new section. To indicate that this is a toolset section, prefix the heading with an exclamation mark.

```aiignore
## !Projects
```

Add an H3 subheading for each resume item. Use an indented preformatted code block to add 2 lines of auxiliary information.

```aiignore
### Gitlytics
    Python, Flask, React, PostgreSQL, Docker
    June 2020 - Present
```

The subheading and auxiliary information will appear from left to right in the compiled document.

Then, use an unordered list to create a description list.

```aiignore
### Gitlytics
    Python, Flask, React, PostgreSQL, Docker
    June 2020 - Present

- Description list item #1
- Description list item #2
```


### Create a catalogue section

Create a new section by adding an H2 heading. A catalogue section contains no resume items, so do not add any H3 subheadings here.

```aiignore
## Technical Skills
```

Create an unordered list. Each item in the unordered list may optionally begin with a label followed by a colon.

```aiignore
## Technical Skills

- Languages: Java, Python, ...
- Another label: Something else, ...
```

Labels are formatted in bold in the compiled document.


### Comments

Any plain text that is not part of a title, contact list, heading, subheading or resume item (i.e. that when translated to HTML does not belong to a tag) will be ignored. This is analogous to comments in most programming languages.


### Hide resume items

You can hide resume sections, resume items, description list items, or catalogue section items. A hidden element will not appear in the compiled document.

To hide a resume section or resume item, prefix its heading or subheading with a caret (```^```).

```aiignore
## ^Education
```

```aiignore
### ^Gitlytics
    Python, Flask, React, PostgreSQL, Docker
    June 2020 - Present

- Description list item #1
- Description list item #2
```

When you do this, the entire resume section or item (not just the heading or subheading) will disappear from the compiled document.

Similarly, to hide a description list item or catalogue section item, simply prefix that item with a caret.

```aiignore
- ^Description list item #1
```

```aiignore
- ^Languages: Java, Python, ...
```



### On escape characters and LaTeX injections.

Some characters have special meaning in LaTeX and should be escaped using backslashes (```\```) when writing Markdown source code. See table below.

| Character |                Escape sequence in Markdown                 |
|:---------:|:----------------------------------------------------------:|
|  ```&```  |                          ```\&```                          |
|  ```%```  |                          ```\%```                          |
|  ```$```  |                          ```\$```                          |
|  ```#```  | ```\#``` in preformatted code blocks, ```\\\#``` otherwise |
|  ```_```  | ```\_``` in preformatted code blocks, ```\\\_``` otherwise |
|  ```{```  | ```\{``` in preformatted code blocks, ```\\\{``` otherwise |
|  ```}```  | ```\}``` in preformatted code blocks, ```\\\}``` otherwise |
|  ```~```  |                   ```\textasciitilde```                    |
|  ```^```  |                   ```\textasciicircum```                   |
|  ```\```  |                    ```\textbackslash```                    |

When necessary, it is possible to inject LaTeX code into Markdown source code (especially in preformatted code blocks). Note, however, that precautions should be taken and escape sequences should be used.


## Compilation

To compile a markdown file in the source directory into a LaTeX file in the destination directory, import the class ```ResumeCompiler```  and create a ```ResumeCompiler``` instance with the source and destination directory paths as arguments. Then, run any one of the methods on the ```ResumeCompiler``` object:
- ```ResumeCompiler.compile(src_file_path, font)``` compiles the file specified by the inputted path.
- ```ResumeCompiler.run(font)``` compiles all Markdown files in the source directory and saves the results in the destination directory, with each LaTeX file in a different subdirectory.
- ```ResumeCompiler.run_with_live_reload(font)``` runs a loop to continuously detect when a Markdown file in the source directory is created or saved. Whenever this happens, that file is compiled with outputs saved in the destination directory.

```aiignore
from resumecompiler import ResumeCompiler

compiler = ResumeCompiler("src", "dist")
compiler.run_with_live_reload()
```

Each of these methods includes an optional ```font``` parameter that determines the typeface used to create the PDF document. This parameter takes an instance of the enum class ```Font```, which can be any of the following.

- ```Font.COMPUTER_MODERN```
- ```Font.TIMES_NEW_ROMAN```
- ```Font.FIRA_SANS```
- ```Font.ROBOTO```
- ```Font.NOTO_SANS```
- ```Font.SOURCE_SANS_PRO```
- ```Font.CORMORANT_GARAMOND```
- ```Font.CHARTER```

The argument defaults to Times New Roman (```Font.TIMES_NEW_ROMAN```). See an example code snippet below.

```
from resumecompiler.Enums.Font import Font
from resumecompiler import ResumeCompiler

compiler = ResumeCompiler("example-src", "example-dist")
compiler.run_with_live_reload(font=Font.TIMES_NEW_ROMAN)
```


### Accessing the Resume object

The compiler works by reading the contents of the input Markdown file and then creating a corresponding ```Resume``` object. To access this internal ```Resume``` object, use the function ```get_resume_object_from_markdown```. The function takes the path to the Markdown source file as input.

```aiignore
resume = get_resume_object_from_markdown('example-src/example.md')
```


## Future improvements

Future improvements with regard to more robust parsing and compilation:

- More user-friendly error handling
- More mature handling of escape characters and LaTeX injection
- UML visualisation of classes