"""JobPilot resume LaTeX preamble (Tectonic-compatible).

Compact, single-page, sans-serif layout: bold uppercase section headers with a
rule, one-line entry headers ("Title • Company" left / "Location | Dates" right),
colored links, and tight vertical spacing so a typical resume stays on one page.
"""

RESUME_LATEX_PREAMBLE = r"""
%-------------------------
% JobPilot Resume Template (Tectonic-compatible, compact one-page)
%-------------------------

\documentclass[letterpaper,10pt]{article}

\usepackage[left=0.45in,right=0.45in,top=0.4in,bottom=0.4in]{geometry}
\usepackage[T1]{fontenc}
% Lato — a clean humanist sans-serif (Calibri-like). Chosen over Carlito because
% Carlito's digit glyphs extract as garbage under Tectonic, which breaks ATS/text
% parsing of phone numbers, dates, and metrics. Lato extracts cleanly.
\usepackage[default]{lato}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage{xcolor}
\usepackage{tabularx}
\usepackage[hidelinks]{hyperref}

\definecolor{linkblue}{HTML}{2148C0}
\hypersetup{colorlinks=true, urlcolor=linkblue, linkcolor=linkblue, breaklinks=true}
\urlstyle{same}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\tabcolsep}{0pt}
\raggedright

% Section: bold, uppercase, full-width rule underneath, tight spacing
\titleformat{\section}{\normalsize\bfseries}{}{0pt}{\MakeUppercase}[\vspace{1pt}\titlerule]
\titlespacing*{\section}{0pt}{7pt}{3pt}

% Tight bullet lists
\setlist[itemize]{leftmargin=1.35em, itemsep=0.6pt, topsep=1pt, parsep=0pt, partopsep=0pt, after=\vspace{1.5pt}}

% One-line entry header: left block flush-left, right block flush-right
\newcommand{\entryrow}[2]{%
  \noindent\begin{tabular*}{\textwidth}{@{}l@{\extracolsep{\fill}}r@{}}#1 & #2\end{tabular*}\par}
"""
