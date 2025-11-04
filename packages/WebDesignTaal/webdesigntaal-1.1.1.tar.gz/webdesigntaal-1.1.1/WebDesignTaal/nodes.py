"""nodes.py

De nodes module geeft definitie's van de verschillende soorten nodes en hoe zij zichzelf renderen.
Ook zorgt het ervoor dat nieuwe nodes worden aangemaakt en het parent/child systeem goed word geregeld.
"""
from typing import Dict, List, Optional

# -------- Variabelen --------
HTML_ATTRIBUTE_KEYS = [
    "id", "class", "href", "src", "alt", "title", "name", "value",
    "type", "placeholder", "checked", "disabled", "readonly", "style",
    "action", "method", "for", "rel", "target", "width", "height", 
    "cols", "rows", "maxlength", "min", "max", "step", "selected",
    "autocomplete", "download", "role", "lang", "tabindex", "aria-label"
]

DUTCH_TRANSLATIONS = {
    "bron": "src",
    "breedte": "width",
    "hoogte": "length",
    "rijen": "rows",
    "kolommen": "cols",
    "taal": "lang",
    "adres": "href",
    "alttekst": "alt",
    "karakterset": "charset",
    "citeer": "cite",
    "verborgen": "hidden"
}

STYLE_PROPERTY_MAP = {
    # kleuren en tekst
    "kleur": "color",
    "achtergrondkleur": "background-color",
    "achtergrond": "background",
    "lettertype": "font-family",
    "lettergrootte": "font-size",
    "letterstijl": "font-style",
    "lettergewicht": "font-weight",
    "tekstuitlijning": "text-align",
    "tekstdecoratie": "text-decoration",
    "teksttransformatie": "text-transform",
    "regelhoogte": "line-height",
    "woordafstand": "word-spacing",
    "letterafstand": "letter-spacing",

    # ruimte & afmetingen
    "breedte": "width",
    "hoogte": "height",
    "marge": "margin",
    "margeboven": "margin-top",
    "margeonder": "margin-bottom",
    "margelinks": "margin-left",
    "margerechts": "margin-right",
    "opvulling": "padding",
    "opvullingboven": "padding-top",
    "opvullingonder": "padding-bottom",
    "opvullinglinks": "padding-left",
    "opvullingrechts": "padding-right",

    # randen
    "rand": "border",
    "randkleur": "border-color",
    "randstijl": "border-style",
    "randdikte": "border-width",
    "afronding": "border-radius",

    # positie
    "positie": "position",
    "boven": "top",
    "onder": "bottom",
    "links": "left",
    "rechts": "right",
    "zweven": "float",
    "weergave": "display",
    "zichtbaarheid": "visibility",
    "zindex": "z-index",

    # effecten
    "schaduw": "box-shadow",
    "tektschaduw": "text-shadow",
    "doorzichtigheid": "opacity",
    "cursor": "cursor",

    # achtergrond
    "achtergrondafbeelding": "background-image",
    "achtergrondpositie": "background-position",
    "achtergrondherhaling": "background-repeat",
    "achtergronddekking": "background-size",

    # animaties
    "animatie": "animation",
    "animatienaam": "animation-name",
    "animatieduur": "animation-duration",
    "overgang": "transition",
}

# ======== Waardevertaling (rood -> red, midden -> center, enz) =========
STYLE_VALUE_MAP = {
    # kleuren
    "rood": "red",
    "blauw": "blue",
    "groen": "green",
    "geel": "yellow",
    "zwart": "black",
    "wit": "white",
    "grijs": "gray",
    "lichtgrijs": "lightgray",
    "donkergrijs": "darkgray",
    "lichtblauw": "lightblue",
    "donkerblauw": "darkblue",
    "lichtgroen": "lightgreen",
    "donkergroen": "darkgreen",
    "lichtrood": "lightred",
    "donkerrood": "darkred",
    "lichtgeel": "lightyellow",
    "donkergeel": "darkyellow",
    "paars": "purple",
    "oranje": "orange",
    "roze": "pink",
    "bruin": "brown",
    "transparant": "transparent",

    # uitlijning
    "links": "left",
    "rechts": "right",
    "midden": "center",
    "gecentreerd": "center",
    "boven": "top",
    "onder": "bottom",

    # display
    "blok": "block",
    "inline": "inline",
    "flex": "flex",
    "geen": "none",

    # font-weight
    "vet": "bold",
    "normaal": "normal",
    "cursief": "italic",

    # positie
    "absoluut": "absolute",
    "relatief": "relative",
    "vast": "fixed",

    # zichtbaarheid
    "verborgen": "hidden",
    "zichtbaar": "visible",

    # border-style
    "stippel": "dotted",
    "gestreept": "dashed",
    "doorgetrokken": "solid",
}




# -------- Node Registry --------
NODE_REGISTRY: Dict[str, type] = {}

def register_node(name: str):
    """Decorator om node classes te registreren in NODE_REGISTRY. 
    Dit is zodat strings bijvoorbeeld makkelijk verbonden kunnen worden met hun 
    respectievelijke class (Node soort)"""
    def deco(cls):
        NODE_REGISTRY[name] = cls
        cls.node_name = name
        return cls
    return deco

# -------- Base Node --------
class BaseNode:
    """Base class voor alle nodes. 
    De class is een verzameling van eigenschappen die elke node met een specifieke class ook heeft. 
    Een voorbeeld hiervan is een lijst van hun childs, parent, attributes, depth en text inhoud"""
    def __init__(self, content: Optional[str] = None, attrs: Optional[Dict] = None, parent: Optional["BaseNode"] = None):
        self.content = content or ""
        self.attrs = attrs or {}
        self.children: List["BaseNode"] = []
        self.parent: Optional["BaseNode"] = parent
        self.depth: int = 0  # 0 = root
        self.position: int = 0  # positie onder parent, 0-indexed, in principe optioneel
        self.tag_name = ""
        self.open = ""
        self.close = ""


        # als er een parent is, voeg jezelf toe aan parent
        if parent:
            parent.append_child(self)

    def update_tags(self):
        html_attrs = {}
        style_attrs = {}

        for k, v in self.attrs.items():
            # Als de attribute een html attribute is voeg hem dan toe
            if k in HTML_ATTRIBUTE_KEYS:
                html_attrs[k] = v
            # Zo niet check of hij een nederlandse vertaling is van een html attribute.
            elif k in DUTCH_TRANSLATIONS:
                html_attrs[DUTCH_TRANSLATIONS[k]] = v
            else:
                # fallback: als key of value niet vertaald is, gebruik originele
                css_key = STYLE_PROPERTY_MAP.get(k.lower(), k)
                css_val = STYLE_VALUE_MAP.get(str(v).lower(), v)
                style_attrs[css_key] = css_val

        if style_attrs:
            style_str = "; ".join(f"{k}:{v}" for k, v in style_attrs.items())
            html_attrs["style"] = style_str

        # na het combineren werk self.attrs bij voor latere attrs req checks
        self.attrs = html_attrs

        attr_str = " ".join(f'{k}="{v}"' for k, v in self.attrs.items())
        self.open = f"<{self.tag_name}{' ' if attr_str else ''}{attr_str}>"
        self.close = f"</{self.tag_name}>"



    def render(self) -> str:
        """
        Render de node met nette indentation op basis van self.depth.
        """
        space = "  " * self.depth  # 2 spaties per level
        content = self.content or ""

        # render children
        children_html = "".join(child.render() for child in self.children)

        # combineer opening tag, children en closing tag
        if children_html:
            return f"{space}{self.open}\n{children_html}{space}{self.close}\n"

        return f"{space}{self.open}{content}{self.close}\n"


    def append_child(self, node: "BaseNode"):
        """Deze functie neemt een node """
        node.parent = self
        node.depth = self.depth + 1
        node.position = len(self.children)
        self.children.append(node)

    def __repr__(self):
        """Weergeeft informatie over de huidige Basenode """
        return f"""<{self.__class__.__name__}
                   depth={self.depth}
                   pos={self.position}
                   content={self.content}>"""

# -------- Concrete Nodes --------


# Het was mogelijk om deze nodes niet apart te maken en de BaseNode te gebruiken maar ik heb expres
# ervoor gekozen om aparte classes ervoor te maken zodat er in de toekomst nog makkelijker verder
# op gebouwd kan worden zonder al te veel werk.


@register_node("document")
class DocumentNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "html"
        self.update_tags()

@register_node("head")
class HeaderNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "head"
        self.update_tags()

@register_node("body")
class BodyNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "body"
        self.update_tags()

@register_node("kop1")
class TitleNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "h1"
        self.update_tags()

@register_node("kop2")
class SubtitleNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "h2"
        self.update_tags()

@register_node("kop3")
class ChapterNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "h3"
        self.update_tags()

@register_node("kop4")
class SubchapterNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "h4"
        self.update_tags()

@register_node("kop5")
class SubsubchapterNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "h5"
        self.update_tags()

@register_node("kop6")
class SubsubsubchapterNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "h6"
        self.update_tags()

@register_node("tekst")
class ParagraphNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "p"
        self.update_tags()

@register_node("opsomming_lijst")
class ListNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "ul"
        self.update_tags()

@register_node("getal_lijst")
class NumberedListNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "ol"
        self.update_tags()

@register_node("lijst_item")
class ListItemNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "li"
        # Check if parent is ListNode or NumberedListNode
        if not (self.parent and isinstance(self.parent, (ListNode, NumberedListNode))):
            raise ValueError("Een lijst item moet onderdeel zijn van een lijst soort.")
        self.update_tags()

@register_node("afbeelding")
class ImageNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "img"
        self.update_tags()
        # Zorg dat er een src attribuut is
        if not self.attrs or "src" not in self.attrs:
            raise ValueError("Afbeeldingen vereisen een 'bron' attribuut!")

@register_node("link")
class LinkNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "a"
        self.update_tags()
        # Zorg dat er een href attribuut is
        if not self.attrs or "href" not in self.attrs:
            raise ValueError("Afbeeldingen vereisen een 'adres' attribuut!")

@register_node("gedeelte")
class SectionNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "div"
        self.update_tags()

@register_node("artikel")
class ArticleNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "article"
        self.update_tags()

@register_node("audio")
class AudioNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "audio"
        self.update_tags()
        # Zorg dat er een src attribuut is
        if not self.attrs or "src" not in self.attrs:
            raise ValueError("Afbeeldingen vereisen een 'bron' attribuut!")

@register_node("video")
class VideoNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "video"
        self.update_tags()
        # Zorg dat er een src attribuut is
        if not self.attrs or "src" not in self.attrs:
            raise ValueError("Afbeeldingen vereisen een 'bron' attribuut!")

@register_node("quote")
class QuoteNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "blockquote"
        self.update_tags()

@register_node("lijn")
class BreakNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "hr"
        self.update_tags()
        self.close = ""

        # Only render self.open when using the breaknode
    def render(self) -> str:
        """
        Render de lijn node met nette indentation op basis van self.depth.
        """
        space = "  " * self.depth  # 2 spaties per level
        content = self.content or ""

        # render children
        children_html = "".join(child.render() for child in self.children)

        # combineer opening tag, children en closing tag
        if children_html:
            return f"{space}{self.open}\n{children_html}\n"

        return f"{space}{self.open}{content}\n"

@register_node("schuingedrukt")
class ItalicNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "i"
        self.update_tags()

@register_node("dikgedrukt")
class BoldNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "b"
        self.update_tags()

@register_node("onderlijndrukt")
class UnderlineNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "u"
        self.update_tags()

@register_node("metadata")
class MetaNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "meta"
        self.update_tags()
    # Only render self.open when using the breaknode
    def render(self) -> str:
        """
        Render de lijn node met nette indentation op basis van self.depth.
        """
        space = "  " * self.depth  # 2 spaties per level
        content = self.content or ""

        # render children
        children_html = "".join(child.render() for child in self.children)

        # combineer opening tag, children en closing tag
        if children_html:
            return f"{space}{self.open}\n{children_html}\n"

        return f"{space}{self.open}{content}\n"

@register_node("tabel")
class TableNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "table"
        self.update_tags()

@register_node("tabelrij")
class TableRowNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "tr"
        self.update_tags()

@register_node("tabelcel")
class TableCellNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "td"
        self.update_tags()

@register_node("stijl")
class StyleNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "link"

        # Set default rel and type
        self.attrs["rel"] = "stylesheet"
        self.attrs["type"] = "text/css"

        self.update_tags()
        self.close = ""
        # Zorg dat er een href attribuut is
        if not self.attrs or "href" not in self.attrs:
            raise ValueError("Stijlcodes vereisen een 'adres' attribuut!")

    def render(self) -> str:
        """
        Render de style node met nette indentation op basis van self.depth en zonder self.close
        """
        space = "  " * self.depth  # 2 spaties per level
        content = self.content or ""

        # render children
        children_html = "".join(child.render() for child in self.children)

        # combineer opening tag, children en closing tag
        if children_html:
            return f"{space}{self.open}\n{children_html}\n"

        return f"{space}{self.open}{content}\n"

@register_node("code")
class ScriptNode(BaseNode):
    def __init__(self, content = None, attrs = None, parent = None):
        super().__init__(content, attrs, parent)
        self.tag_name = "script"
        self.update_tags()
        # Zorg dat er een src attribuut is
        if not self.attrs or "src" not in self.attrs:
            raise ValueError(f"scripts vereisen een 'bron' attribuut! {self.attrs}")

    def render(self) -> str:
        """
        Render de script node met nette indentation op basis van self.depth en zonder self.close
        """
        space = "  " * self.depth  # 2 spaties per level
        content = self.content or ""

        # render children
        children_html = "".join(child.render() for child in self.children)

        # combineer opening tag, children en closing tag
        if children_html:
            return f"{space}{self.open}\n{children_html}{self.close}\n"

        return f"{space}{self.open}{content}{self.close}\n"


# -------- Factory --------
def create_node(kind: str, **kwargs) -> BaseNode:
    """Een functie die gemaakt is om een node aan te maken. 
    Hij kijkt of de soort node bestaat in de NODE_REGISTRY 
    Zo ja neemt hij de gegeven class en maakt een nieuwe node aan met de gegeven parameters"""
    cls = NODE_REGISTRY.get(kind)
    if not cls:
        raise KeyError(f"Unknown node type: {kind}. Available: {list(NODE_REGISTRY.keys())}")
    return cls(**kwargs)

# -------- Demo / Test --------
if __name__ == "__main__":
    doc = create_node("document")
    h1 = create_node("kop1", content="Welkom!", parent=doc)
    p = create_node("tekst", content="Dit is een paragraaf.", parent=doc)
    ul = create_node("opsomming_lijst", parent=doc)
    li1 = create_node("lijst_item", content="Appel", parent=ul)
    li2 = create_node("lijst_item", content="Banaan", attrs={"color": "red"}, parent=ul)
    nod1 = create_node("stijl", attrs={"adres": "stylesheet.css"}, parent=doc)
    print(doc.render())
