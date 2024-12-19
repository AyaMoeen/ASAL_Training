import random
from typing import Union, List, Optional
HTMLElementValue = Union[str,'HTMLElement', list['HTMLElement']]

class HTMLElement:
    VALID_TAGS = {
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'p', 'table', 'tr', 'td', 'th',
        'href', 'link', 'label', 'input', 'button', 'form', 'nav', 'body', 'style',
        'script', 'html', 'header', 'span', 'div',
    }
 
    def __init__(
        self, name: str, value: HTMLElementValue, attrs: Optional[dict] = None
    ) -> None:
        """ constructor: initialize instance of HTMLElement  """ 
        if name not in HTMLElement.VALID_TAGS:
            raise Exception(f'{name} not vaild name of tag in the HTML')
        self.attrs = attrs if attrs is not None else {}  
        self.value: List[Union[str, 'HTMLElement']] = []
        self.name = name
        self.ids = set() 
        self.parent: Optional['HTMLElement'] = None
        if 'id' in self.attrs:
            self.ids.add(self.attrs['id'])
        HTMLElement.append(self, value)
       
    @classmethod
    def append(cls, parent: 'HTMLElement', child: HTMLElementValue) -> None: 
        """ Append instance of Element or sub tree to tree """
        if isinstance(child, str):
            parent.value = [child]
        elif isinstance(child,list):
            for ch in child:
                cls.append(parent,ch)
        elif isinstance(child,HTMLElement): 
            if 'id' in child.attrs:
                for id in child.ids:
                    if parent.check_update_id(id): 
                        raise Exception('Duplicate ID, Faild to append')
            child.parent = parent
            parent.value.append(child)
            
            """ or using update:  parent.ids.update(child.ids)  """ 
            parent.ids = parent.ids.union(child.ids)
            
    def check_update_id(self, id: str) -> bool: 
        """ 
        check if the id of element or ids of subtree found in tree 
        then add the id to set of ids
        """
        if id is None:                              
            return False
        if id in self.ids:
            self.ids.remove(id) 
            return True
        temp: Optional['HTMLElement'] = self.parent
        if temp:
            return temp.check_update_id(id)
        self.ids.add(id) 
        if self.parent:
            self.parent.ids.add(id)
        return False


    @classmethod
    def render(cls, element:'HTMLElement', space:int=0) -> str:
        """  render the html element and its own sub-elements as specif format """
        if element is None:
            return 'the element empty'
        indent = " " * space
        attribute = ' '.join(f'{key}="{val}"' for key, val in element.attrs.items())
        tag_open = f'<{element.name} {attribute.strip()}>' if attribute else f'<{element.name}>'
        tag_close = f'</{element.name}>'
        string_child = '\n'.join(cls.render(ch,space + 4) for ch in element.value if isinstance(ch, HTMLElement))
        val = ''.join(str(v) for v in element.value if isinstance(v, str))
        return f'{indent}{tag_open}{val}\n{string_child}{indent}{tag_close}\n'

    @classmethod
    def find_element_by_tag_name(cls, html_element: 'HTMLElement', name: str) -> List['HTMLElement']:
        """ find element by tage name """
        results = []
        if html_element.name == name:
            results.append(html_element)        
        for child in html_element.value:
            if isinstance(child, HTMLElement):
                results.extend(cls.find_element_by_tag_name(child, name))
        return results

    @classmethod
    def find_element_by_attrs(cls, html_element: 'HTMLElement', attr: str, value: str) -> List['HTMLElement']:
        """ find element by attrs """
        results = []
        if html_element.attrs.get(attr) == value:
            results.append(html_element)
        for child in html_element.value:
            if isinstance(child, HTMLElement):
                results.extend(cls.find_element_by_attrs(child, attr, value))
        return results

    @classmethod
    def render_html_file(cls, root:'HTMLElement') -> str:
        """ render html to file, have the DOCTYPE """
        result_html = "<!DOCTYPE html>\n<html>\n"
        result_html += cls.render(root, space=4)
        result_html += "</html>\n"
        with open("index.html", "w") as file_html:
            file_html.write(result_html)
        return result_html

    @classmethod
    def remove(cls, root: 'HTMLElement', subtree_to_remove: 'HTMLElement') -> Union['HTMLElement', None]:
        """ 
        remove the element or sub tree from tree and remove any ids of sub tree
        like seperate it to two tree 
        """
        if root.value is None:
            return None
        if subtree_to_remove in root.value:              
            root.ids.difference_update(subtree_to_remove.ids)
            root.value.remove(subtree_to_remove)
            return  subtree_to_remove
        for ch in root.value:
            if isinstance(ch, HTMLElement):
                res = cls.remove(ch, subtree_to_remove)
                if res:
                    root.ids.difference_update(subtree_to_remove.ids)
                    return res
        return None

    
        
    @classmethod
    def clone(cls, p: Optional['HTMLElement'] = None, element: Optional['HTMLElement'] = None) -> 'HTMLElement':
        """ duplicate the tree with unique attrs"""
        if element is None:
            raise ValueError('cant be none')
        attr_clone = {}
        for key, value in element.attrs.items():
            attr_clone[key] = value + f'_clone{random.randint(1, 100)}'
        child = [ch for ch in element.value if isinstance(ch, HTMLElement)]
        value_of_str = ''.join(ch for ch in element.value if isinstance(ch, str))
        element_clone = HTMLElement(element.name, child, attrs=attr_clone)
        if value_of_str:
            element_clone.value.append(value_of_str)
            
        for ch in child:
            child_clone = cls.clone(element_clone, ch)
            HTMLElement.append(element_clone, child_clone)
        return element_clone
    
    
    def to_dict(self) -> dict:
        """ convert html to json """
        dict_html = {
            "name": self.name,
            "value": self.value if isinstance(self.value, str) else None,
            "attrs": self.attrs,
            "children": [
                ch.to_dict() if isinstance(ch, HTMLElement) else ch
                for ch in self.value
                ]
        }
        return dict_html
    
    @classmethod   
    def from_dict(cls, element_json: dict) -> 'HTMLElement':  
        """ convert json to html element or tree"""          
        element = HTMLElement(element_json['name'], value=element_json['value'], attrs=element_json['attrs'])
        for ch in element_json['children']:
            child = HTMLElement(ch['name'],ch['value'],ch['attrs'])
            cls.append(element,child)
        return element
    
