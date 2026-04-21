import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class UIElement:
    text: str
    content_desc: str
    resource_id: str
    class_name: str
    clickable: bool
    focusable: bool
    bounds: tuple[int, int, int, int]  # x1, y1, x2, y2
    children: list["UIElement"]

    @property
    def center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.bounds
        return (x1 + x2) // 2, (y1 + y2) // 2

    def __repr__(self) -> str:
        label = self.text or self.content_desc or self.resource_id or self.class_name
        return f"UIElement({label!r}, bounds={self.bounds}, clickable={self.clickable})"


def _parse_bounds(bounds_str: str) -> tuple[int, int, int, int]:
    # Format: [x1,y1][x2,y2]
    parts = bounds_str.replace("][", ",").strip("[]").split(",")
    return int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])


def _parse_node(node: ET.Element) -> UIElement:
    return UIElement(
        text=node.get("text", ""),
        content_desc=node.get("content-desc", ""),
        resource_id=node.get("resource-id", ""),
        class_name=node.get("class", ""),
        clickable=node.get("clickable", "false") == "true",
        focusable=node.get("focusable", "false") == "true",
        bounds=_parse_bounds(node.get("bounds", "[0,0][0,0]")),
        children=[_parse_node(child) for child in node],
    )


def parse(xml_str: str) -> UIElement:
    root = ET.fromstring(xml_str)
    hierarchy_root = root if root.tag != "hierarchy" else list(root)[0]
    return _parse_node(hierarchy_root)


def find_all(element: UIElement, text: str | None = None, content_desc: str | None = None,
             resource_id: str | None = None, clickable_only: bool = False) -> list[UIElement]:
    results = []

    def _match(el: UIElement) -> bool:
        if clickable_only and not el.clickable:
            return False
        if text and text.lower() not in el.text.lower():
            return False
        if content_desc and content_desc.lower() not in el.content_desc.lower():
            return False
        if resource_id and resource_id not in el.resource_id:
            return False
        return any([
            text and el.text,
            content_desc and el.content_desc,
            resource_id and el.resource_id,
        ])

    def _walk(el: UIElement) -> None:
        if _match(el):
            results.append(el)
        for child in el.children:
            _walk(child)

    _walk(element)
    return results


def find_first(element: UIElement, **kwargs) -> UIElement | None:
    results = find_all(element, **kwargs)
    return results[0] if results else None


def to_text(element: UIElement, indent: int = 0) -> str:
    """Produce a compact readable summary of the UI hierarchy."""
    lines = []

    def _walk(el: UIElement, depth: int) -> None:
        label = el.text or el.content_desc
        short_id = el.resource_id.split("/")[-1] if "/" in el.resource_id else el.resource_id
        short_class = el.class_name.split(".")[-1]
        flags = []
        if el.clickable:
            flags.append("tap")
        if el.focusable:
            flags.append("focus")
        flag_str = f" [{','.join(flags)}]" if flags else ""
        cx, cy = el.center
        if label or el.clickable:
            lines.append(
                f"{'  ' * depth}{short_class}"
                + (f' "{label}"' if label else "")
                + (f" #{short_id}" if short_id else "")
                + flag_str
                + f" @({cx},{cy})"
            )
        for child in el.children:
            _walk(child, depth + 1)

    _walk(element, indent)
    return "\n".join(lines)
