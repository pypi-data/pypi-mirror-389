# tree version
def parse_tree_structure(lines):
    result = []
    stack = [(0, result)]
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        clean_line = line.replace("├──", "").replace("│", "").replace("└──", "")
        indent = len(line) - len(clean_line)
        clean_line = clean_line.strip()
        if not clean_line:
            continue
        node = {"name": clean_line, "children": []}
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(0, result)]
        stack[-1][1].append(node)
        stack.append((indent, node["children"]))
    return result

# blank version
def parse_indent_structure(lines):
    tree = []
    stack = [(-1, tree)]
    for line in lines:
        stripped = line.rstrip('\n')
        if not stripped.strip():
            continue
        indent = len(line) - len(line.lstrip())
        node = {"name": stripped.strip(), "children": []}
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(-1, tree)]
        stack[-1][1].append(node)
        stack.append((indent, node["children"]))
    return tree
