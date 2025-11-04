"""wdt_parser.py
In this file you will find the code that parses all the text and creates a tree of nodes.
When finished creating the tree it will render the root node. which in turn will 
render all the children. After this it returns the HTML code.
"""
from typing import List, Tuple, Dict

from . import nodes # nodes.py
from .updater import get_local_version


SPACE_INDENT_SIZE = 4

def split_first_unquoted(s: str, sep: str = ';') -> Tuple[str, str]:
    """Split s on the first sep that is not inside quotes. Return (left, right)."""
    in_quote = False
    quote_char = ''
    esc = False
    for i, ch in enumerate(s):
        if esc:
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if in_quote:
            if ch == quote_char:
                in_quote = False
                quote_char = ''
            continue
        else:
            if ch in ('"', "'"):
                in_quote = True
                quote_char = ch
                continue
            if ch == sep:
                left = s[:i]
                right = s[i+1:]
                return left, right

    raise ValueError("Geen scheiding gevonden. Ben je ; vergeten?")  # no separator found

def tokenize_attrs(attr_str: str) -> List[str]:
    """Split attr_str into tokens on whitespace or ';', respecting quotes."""
    tokens: List[str] = []
    cur = []
    in_quote = False
    quote_char = ''
    esc = False
    for ch in attr_str:
        if esc:
            cur.append(ch)
            esc = False
            continue
        if ch == '\\':
            esc = True
            continue
        if in_quote:
            if ch == quote_char:
                in_quote = False
                quote_char = ''
                # keep closing quote out of token (we'll strip later)
            else:
                cur.append(ch)
            continue
        # not in quote
        if ch in ('"', "'"):
            in_quote = True
            quote_char = ch
            continue
        if ch.isspace() or ch == ';':
            if cur:
                tokens.append(''.join(cur))
                cur = []
            # skip multiple separators
            continue
        cur.append(ch)
    if cur:
        tokens.append(''.join(cur))
    return tokens

def parse_attrs_from_left(left: str) -> Dict[str,str]:
    """
    left: e.g. "p color=red class=foo" or "a href=\"https://...\"" as seen in split_first_unquoted()
    returns dict of attrs (node type not included).
    Note: caller should separate nodetype from left first.
    """
    tokens = tokenize_attrs(left)
    attrs: Dict[str,str] = {}
    for tok in tokens:
        if '=' in tok:
            k, v = tok.split('=', 1)
            k = k.strip()
            v = v.strip()
            # strip surrounding quotes if present
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            attrs[k] = v
        else:
            # bare token like "disabled" -> set true
            attrs[tok] = "true"
    return attrs

def detect_indent_style(lines: List[str]) -> str:
    "Detects if indentation is spaces or tabs"
    for l in lines:
        if l.startswith("\t"):
            return "tabs"
    return "spaces"

def get_depth(line: str, indent_style: str) -> int:
    "Get depth amount in tabs or spaces"
    if indent_style == "tabs":
        count = 0
        for ch in line:
            if ch == '\t':
                count += 1
            else:
                break
        return count
    else:
        # spaces
        count = 0
        for ch in line:
            if ch == ' ':
                count += 1
            else:
                break
        return count // SPACE_INDENT_SIZE

def parse_lines_to_tree(lines: List[str]) -> Tuple[nodes.BaseNode, List[str]]:
    """
    Parse lines with semicolon syntax into a node tree using nodes.create_node.
    Returns (root_node, errors).
    """
    errors: List[str] = []
    indent_style = detect_indent_style(lines)

    root = nodes.create_node("document")
    stack: List[nodes.BaseNode] = [root]  # stack[depth] = node at that depth
    del root # Cleanup root node

    for lineno, raw in enumerate(lines, start=1):
        # ignore blanks and comments (#)
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        depth = get_depth(raw, indent_style)
        # remove leading indent characters
        if indent_style == "tabs":
            trimmed = raw.lstrip('\t').rstrip("\n").rstrip("\r")
        else:
            trimmed = raw.lstrip(' ').rstrip("\n").rstrip("\r")

        # split on first unquoted semicolon
        left, content = split_first_unquoted(trimmed, ';')
        left = left.strip()
        content = content.lstrip()

        if not left:
            errors.append(f"Line {lineno}: mist een node type / linker kant")
            continue

        # nodetype is the first token of left
        parts = left.split(None, 1)
        nodetype = parts[0]
        attr_segment = parts[1] if len(parts) > 1 else ""

        # parse attrs from attr_segment
        attrs = {}
        if attr_segment:
            try:
                attrs = parse_attrs_from_left(attr_segment)
            except Exception as e:
                errors.append(f"Line {lineno}: attribute parse error: {e}")

        # determine parent
        if depth > len(stack) - 1:
            errors.append(f"Line {lineno}: foute indentatie (diepte {depth}), Node word child van meest recente parent node")
            parent = stack[-1]
        else:
            parent = stack[depth]

        # create node
        try:
            node = nodes.create_node(nodetype, content=content, attrs=attrs, parent=parent)
            # ensure tags updated if needed
            try:
                node.update_tags()
            except Exception:
                errors.append(f"Line {lineno}: Error bij het updaten van de tags voor de node '{nodetype}'")
        except KeyError:
            errors.append(f"Line {lineno}: onbekend tag type '{nodetype}'")
            continue
        except Exception as e:
            errors.append(f"Line {lineno}: error bij het aanmaken van een node '{nodetype}': {e}")
            continue

        # update stack
        stack = stack[: depth + 1 ]
        stack.append(node)

    return stack[0], errors


def render_code(code: str) -> str:
    """Neemt de ruwe code (string met \\n) en rendert het volledige HTML-resultaat."""
    root, errors = parse_lines_to_tree(code.splitlines())   # gebruik jouw bestaande parser
    if errors:
        print("Error: ")
        return "\n".join(errors)
    return f"<!DOCTYPE html>\n<!-- WebDesignTaal (v{get_local_version()}) -->\n" + root.render()      # render alle nodes tot HTML