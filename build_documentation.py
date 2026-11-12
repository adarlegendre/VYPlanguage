"""Generate documentation.pdf for the VYPa submission."""

from fpdf import FPDF


class Doc(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def h1(pdf, text):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, text)
    pdf.ln(2)


def h2(pdf, text):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(0, 7, text)
    pdf.ln(1)


def body(pdf, text):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, text)
    pdf.ln(1)


def bullet(pdf, text):
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, f"- {text}")
    pdf.ln(1)


def main():
    pdf = Doc()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_left_margin(18)
    pdf.set_right_margin(18)
    pdf.add_page()

    # --- Title page content (required) ---
    h1(pdf, "VYPa Compiler Project Documentation")
    body(
        pdf,
        "VYPlanguage to VYPcode compiler implemented in Python with PLY.",
    )
    h2(pdf, "Authors and points division")
    body(
        pdf,
        "AUTHOR_NAME_1 (xlogin01) - 50%\n"
        "AUTHOR_NAME_2 (xlogin02) - 50%\n\n"
        "Replace the placeholders above and in the division file with the real "
        "team names and FIT logins before submission. The submitted archive "
        "must contain a division file whose percentages sum to 100.",
    )
    h2(pdf, "Implemented extensions")
    body(
        pdf,
        "No registered bonus extensions are claimed in this submission "
        "(no extensions file). The base language from vypa25.pdf is the target, "
        "including objects/classes required by the specification examples.",
    )

    # --- Front-end ---
    pdf.add_page()
    h1(pdf, "1. Compiler front-end")
    h2(pdf, "1.1 Tools and overall pipeline")
    body(
        pdf,
        "The compiler is a command-line tool named vypcomp. It reads a "
        "VYPlanguage source file and writes VYPcode (default out.vc). "
        "Exit codes follow the project specification: 0, 11 (lexical), "
        "12 (syntax), 13 (semantic type), 14 (other semantic), 15 (codegen), "
        "19 (internal). The compiler writes diagnostics only to stderr and "
        "keeps stdout silent so automatic diff evaluation of interpreted "
        "programs is not disturbed.",
    )
    body(
        pdf,
        "Implementation language: Python 3. Lexical and syntactic analysis "
        "use PLY (Python Lex-Yacc). The phases are: lexer -> parser (AST) -> "
        "semantic analysis with symbol table -> three-address IR -> VYPcode "
        "generation.",
    )

    h2(pdf, "1.2 Lexical analysis")
    body(
        pdf,
        "src/lexer.py implements a PLY lex scanner. It recognizes keywords "
        "(class, else, if, int, new, return, string, super, this, void, while), "
        "identifiers, integer literals, string literals with common escapes, "
        "operators, and delimiters. Line and block comments are discarded. "
        "Illegal characters produce exit code 11.",
    )

    h2(pdf, "1.3 Grammar and syntactic analysis")
    body(
        pdf,
        "src/parser.py implements an LALR(1) grammar with PLY yacc. The "
        "program is a sequence of global function and class definitions. "
        "Important design choices:",
    )
    bullet(
        pdf,
        "Literals are tagged in the AST as int_lit / str_lit / var so later "
        "phases can distinguish strings from identifiers after quote stripping.",
    )
    bullet(
        pdf,
        "Class members share a data_type IDENTIFIER prefix; a class_member_tail "
        "disambiguates fields (int x;) from methods (int foo(void){...}).",
    )
    bullet(
        pdf,
        "Field assignment expression.field = expr is supported alongside "
        "ordinary assignment.",
    )
    bullet(
        pdf,
        "Operator precedence follows Table 1 of the language specification.",
    )
    body(
        pdf,
        "Syntax errors are reported on stderr and abort compilation with "
        "exit code 12.",
    )

    h2(pdf, "1.4 Semantic analysis and symbol table")
    body(
        pdf,
        "Semantic checks live in src/compiler.py and use src/symbol_table.py. "
        "A two-pass approach declares all global functions and classes first "
        "(supporting use-before-definition / mutual recursion), then checks "
        "bodies. The symbol table tracks stacked scopes, functions, classes, "
        "and the built-in Object root. Embedded functions print, readInt, "
        "readString, length, and subStr are predeclared. print is treated as "
        "vararg. Missing main or wrong main signature yields semantic error 14.",
    )

    # --- Back-end ---
    pdf.add_page()
    h1(pdf, "2. Compiler back-end")
    h2(pdf, "2.1 Intermediate representation")
    body(
        pdf,
        "src/intermediate_representation.py builds three-address IR from the "
        "AST: assignments, binary/unary ops, labels, jumps, calls, returns, "
        "object creation, field get/set, and method calls. Type tracking "
        "distinguishes int vs string (and class names for object references) "
        "so string concatenation and comparisons lower differently from "
        "integer arithmetic. Methods are emitted as Class:method callables "
        "with a hidden this parameter.",
    )

    h2(pdf, "2.2 VYPcode generation and memory model")
    body(
        pdf,
        "src/vypcode_generator.py emits VYPcode 1.0. Program startup builds "
        "virtual method tables (VMTs) on the stack, then CALL main and JUMP "
        "_end so termination does not loop. Each function uses a BP-relative "
        "stack frame: saved BP, return PC, parameters below BP, locals/temps "
        "above BP. The calling convention matches the interpreter rules for "
        "CALL/RETURN with the return value occupying the first parameter slot.",
    )
    body(
        pdf,
        "Registers: $0=BP, $1=AX scratch, $2-$3/$5-$7 additional scratch "
        "($4=OBJ for method receivers). Strings are heap chunks created with "
        "CREATE/SETWORD/GETWORD; print uses WRITES/WRITEI; readInt/readString "
        "use READI/READS.",
    )

    h2(pdf, "2.3 Runtime helpers and objects")
    body(
        pdf,
        "Embedded string operations are implemented as helper labels: length, "
        "subStr, and __str_concat__. Object support (src/class_model.py) "
        "computes field offsets and VMTs. Object layout: word0=VMT, "
        "word1=parent VMT, word2=class name, then fields (inherited first). "
        "new allocates the object, default-initializes fields, and runs the "
        "constructor chain from ancestor to child. Method calls push this "
        "(and args), load a function label from the VMT (or parent VMT for "
        "super), and CALL dynamically. Object:toString / Object:getClass "
        "are provided as built-in labels.",
    )

    h2(pdf, "2.4 Optimizations")
    body(
        pdf,
        "No separate optimization pass is claimed. Practical choices that "
        "reduce code size/complexity include: reusing expression scratch "
        "registers, emitting helpers only when referenced, and keeping "
        "locals in stable BP slots (required for correct recursion anyway).",
    )

    # --- Work division / running ---
    pdf.add_page()
    h1(pdf, "3. Work division")
    body(
        pdf,
        "Update this section with the real split before hand-in. Suggested "
        "baseline reflecting the current repository structure:",
    )
    bullet(pdf, "Front-end (lexer, parser, AST shaping, semantic/symbol table)")
    bullet(pdf, "IR generation and control-flow / expression lowering")
    bullet(pdf, "VYPcode frames, embedded IO/strings, object/VMT backend")
    bullet(pdf, "Testing against vypint and submission packaging/docs")
    body(
        pdf,
        "Both team members should review the full pipeline. Adjust the "
        "division file if effort is not equal.",
    )

    h1(pdf, "4. Building and running on Merlin")
    body(
        pdf,
        "Requirements: Python 3 with PLY, and the course interpreter "
        "vypint-1.0.jar (also available under /pub/courses/vyp/vypint on "
        "Merlin).",
    )
    body(
        pdf,
        "Setup and compile:",
    )
    body(
        pdf,
        "  make install\n"
        "  make\n"
        "  ./vypcomp input.vyp output.vc\n"
        "  java -jar vypint-1.0.jar output.vc",
    )
    body(
        pdf,
        "If the second argument is omitted, the compiler writes out.vc. "
        "make test compiles the core example programs into build/*.vc.",
    )

    h1(pdf, "5. Testing notes")
    body(
        pdf,
        "The tests/ directory includes the specification examples "
        "(iterative/recursive factorial, strings, classes) plus arithmetic "
        "cases. Evaluation is performed by compiling with vypcomp and "
        "running the result under vypint, comparing stdout with diff. "
        "Some older scratch tests that use non-language syntax (e.g. var) "
        "are not part of the graded example set.",
    )

    h1(pdf, "6. Literature")
    bullet(pdf, "Krivka, Kocman, Regeciova - VYPa: The Compiler Project Specification (vypa25.pdf), 2025.")
    bullet(pdf, "PLY (Python Lex-Yacc) documentation - https://www.dabeaz.com/ply/")
    bullet(pdf, "Course materials and forum of VYPa, FIT VUT Brno.")
    bullet(pdf, "Aho, Sethi, Ullman - Compilers: Principles, Techniques, and Tools (general background).")

    pdf.output("documentation.pdf")
    print("Wrote documentation.pdf")


if __name__ == "__main__":
    main()
