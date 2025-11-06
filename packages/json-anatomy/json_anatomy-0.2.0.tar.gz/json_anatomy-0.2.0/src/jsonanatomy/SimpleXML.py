"""
Simple XML to dictionary converter.

This module provides a utility class for parsing XML strings and converting
them to nested dictionary structures for easier JSON-like manipulation.
Built on lxml for high performance and robust parsing with automatic handling
of malformed XML and fragments.
"""

from lxml import etree as ET
from lxml import html

class SimpleXML:
    """
    A utility class for converting XML strings to nested dictionary structures.

    This class provides robust XML parsing capabilities powered by lxml, with
    automatic handling of well-formed XML, XML fragments, and malformed markup.
    It converts XML elements to nested dictionaries and provides tag usage analysis.

    **Parsing Strategy:**
    1. Attempts strict XML parsing with lxml.etree
    2. Falls back to lenient HTML parsing for malformed XML
    3. Automatically wraps XML fragments (missing root tags) as needed
    4. Preserves tag case when using strict XML mode

    Parameters
    ----------
    xml_string : str
        The XML/HTML string to parse and convert. Can be well-formed XML,
        XML fragments without a root tag, or malformed HTML-like markup.

    Attributes
    ----------
    data : str
        The original XML string.
    root : lxml.etree._Element
        The parsed XML/HTML root element.

    Notes
    -----
    This class uses lxml for parsing, which provides:
    - High performance C-based parsing
    - Robust error recovery for malformed markup
    - Support for XML fragments and HTML5
    - XPath and advanced XML features (accessible via root attribute)

    Examples
    --------
    Well-formed XML:
    
    >>> xml_data = '<users><user><name>Alice</name><age>30</age></user></users>'
    >>> parser = SimpleXML(xml_data)
    >>> result = parser.to_dict()
    >>> print(result)
    {'user': {'name': 'Alice', 'age': '30'}}
    
    XML fragments (automatically wrapped):
    
    >>> fragment = '<item>One</item><item>Two</item>'
    >>> parser = SimpleXML(fragment)
    >>> result = parser.to_dict()
    >>> print(result)  # Wrapped in synthetic root
    {'item': 'One'}
    
    Malformed HTML-like markup (lenient parsing):
    
    >>> malformed = '<div><p>Text<br><span>More</span></div>'
    >>> parser = SimpleXML(malformed)
    >>> result = parser.to_dict()  # Handles unclosed <br>
    """
    def __init__(self, xml_string):
        self.data = xml_string
        if not self.data:
            self.root = None
            return
            
        # Try parsing as strict XML first
        try:
            self.root = ET.fromstring(self.data)
        except ET.XMLSyntaxError:
            # Try HTML parser for malformed XML (with existing root)
            try:
                self.root = html.fromstring(self.data)
            except Exception:
                # If that fails, try wrapping in a root tag with XML parser
                try:
                    wrapped = f'<root>{self.data}</root>'
                    self.root = ET.fromstring(wrapped)
                except ET.XMLSyntaxError:
                    # Last resort: wrap and use HTML parser
                    wrapped = f'<root>{self.data}</root>'
                    self.root = html.fromstring(wrapped)

    def to_dict(self):
        """
        Convert the XML structure to a nested dictionary.

        Returns
        -------
        dict
            A nested dictionary representation of the XML structure.
            Text content becomes string values, and nested elements become
            nested dictionaries.

        Examples
        --------
        >>> xml_data = '<person><name>John</name><age>25</age></person>'
        >>> parser = SimpleXML(xml_data)
        >>> result = parser.to_dict()
        >>> print(result)
        {'name': 'John', 'age': '25'}
        """
        return self._element_to_dict(self.root)

    def _element_to_dict(self, element):
        """
        Recursively convert an XML element to a dictionary.

        Parameters
        ----------
        element : lxml.etree._Element or None
            The XML element to convert.

        Returns
        -------
        dict or str or None
            A dictionary for elements with children, a string for text content,
            or None for empty elements.
        """
        if element is None:
            return None

        result = {}
        for child in element:
            result[child.tag] = self._element_to_dict(child)

        if not result:
            return element.text

        return result
    
    def analyze_tag_usagee(self):
        """
        Analyze the frequency of XML tags in the document.

        Returns
        -------
        dict
            A dictionary mapping tag names to their occurrence counts.

        Examples
        --------
        >>> xml_data = '<root><item>1</item><item>2</item><name>test</name></root>'
        >>> parser = SimpleXML(xml_data)
        >>> counts = parser.analyze_tag_usagee()
        >>> print(counts)
        {'root': 1, 'item': 2, 'name': 1}

        Notes
        -----
        The method name contains a typo ('usagee' instead of 'usage') but is
        preserved for backward compatibility.
        """
        tag_counts = {}
        self._count_tags(self.root, tag_counts)
        return tag_counts
    
    def _count_tags(self, element, tag_counts):
        """
        Recursively count occurrences of each XML tag.

        Parameters
        ----------
        element : lxml.etree._Element
            The XML element to process.
        tag_counts : dict
            Dictionary to store tag counts (modified in place).
        """
        if element.tag in tag_counts:
            tag_counts[element.tag] += 1
        else:
            tag_counts[element.tag] = 1
        
        for child in element:
            self._count_tags(child, tag_counts)
